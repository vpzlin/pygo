import sys
import os
import sqlite3
import threading
import paramiko
import time
import re
import json
import logging
from queue import Queue
from datetime import datetime

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(filename)s line:%(lineno)d | %(message)s',
                    level=logging.INFO)

"""
set running parameters
"""
conn: sqlite3.Connection  # sqlite数据库连接
sleep_interval_seconds = 10  # 生产者间隔（单位：秒）
db_filename = 'server_loads_info.db'  # sqlite数据文件
records_remain_days = 90  # 记录保留时间（单位：天）

data_of_server_loads = Queue()  # 服务器负载数据队列

# 字段间隔符
space_mark = '|@|'


def do_multi_sql(sql: str):
    """
    执行SQL
    :param sql: SQL语句
    :return:
    """
    cursor = conn.cursor()
    cursor.executescript(sql)
    cursor.close()
    conn.commit()


def do_sql(sql: str):
    """
    执行SQL
    :param sql: SQL语句
    :return:
    """
    cursor = conn.cursor()
    cursor.execute(sql)

    values = cursor.fetchall()

    cursor.close()
    conn.commit()

    return values


def init_db_tables():
    """
    初始化数据库表
    :return: None
    """
    file_create_tables_sql = 'create_tables.sql'
    try:
        with open(file_create_tables_sql, mode='rb') as file:
            sql = file.read().decode().replace('\r', '\n')
            do_multi_sql(sql)
            logging.info('初始化SQLite数据库文件[{0}]完毕。'.format(db_filename))
    except Exception as e:
        logging.error('初始化SQLite数据库文件[{0}]失败，程序退出！{1}\n'.format(db_filename, str(e)))
        sys.exit(1)


def tip_for_input():
    """
    输入参数提示
    :return: 
    """
    tip = '    运行方法： python3 {0} start | stop | load_servers server_list_file    \n' \
          '    参数说明： start                      -->  启动脚本                     \n' \
          '             stop                       -->  停止脚本                     \n' \
          '             load_servers server_list_file  -->  载入服务器列表，server_list_file为列表文件，每台服务器一行一个'.format(sys.argv[0])
    print(tip)


def start_collect():
    """
    开始搜集服务器负载信息
    :return:
    """
    while True:
        num = 0  # 计数器
        results = do_sql("select server, username, password from server_list where enable = 1")

        """ 收集负载数据 """
        scan_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 收集负载信息的线程
        for server, username, password in results:
            logging.debug('开始搜集服务器[{0}]的负载。'.format(server))
            t_scan = threading.Thread(target=get_info, args=(scan_dt, server, username, password))
            t_scan.start()

        """ 保存负载数据到SQLite中 """
        while num < len(results):
            while data_of_server_loads.empty() is False:
                data = data_of_server_loads.get()
                save_data_to_db(data)
                num += 1
            time.sleep(3)

        """ 清除历史数据 """
        do_sql("delete from server_loads where scan_dt < date('now', '-{0} day');".format(0))
        do_sql("VACUUM")
        logging.info('删除了表 server_loads 中字段 scan_dt 值是 {0} 天前的数据。'.format(records_remain_days))

        # 进程休眠
        logging.debug('本轮收集负载信息完毕，扫描进程休眠 {0} 秒...'.format(sleep_interval_seconds))
        time.sleep(sleep_interval_seconds)


def get_info_uptime(ssh: paramiko.SSHClient):
    """
    解析uptime命令的字符串
    :param ssh:
    :return:
    """
    results: dict = {}
    std_in, std_out, std_err = ssh.exec_command('uptime')
    res, err = std_out.read(), std_err.read()
    result_uptime = bytes.decode(res if res else err).strip()

    args = re.sub(' +', ' ', result_uptime.strip()).split(',')
    results['uptime_load_average_15min'] = args.pop()
    results['uptime_load_average_5min'] = args.pop()
    results['uptime_load_average_1min'] = args.pop().split(' ').pop()
    results['uptime_user_connections'] = args.pop().strip().split(' ')[0]
    args1 = args[0].split(' ')
    del args1[0]  # 删除当前时间
    del args1[0]  # 删除'up'字符串
    args[0] = ' '.join(args1)  # 系统运行时间
    results['result_uptime_runtime'] = re.sub(' +', ' ', ' '.join(args))
    return results


def get_info_free_mb(ssh: paramiko.SSHClient):
    results: dict = {}
    std_in, std_out, std_err = ssh.exec_command('free -m')
    res, err = std_out.read(), std_err.read()
    result_free_mb = bytes.decode(res if res else err).strip()

    lines = re.sub(' +', ' ', result_free_mb).split('\n')
    args_mem = re.sub(' +', ' ', lines[1]).split(' ')
    args_mem_swap = re.sub(' +', ' ', lines[2]).split(' ')
    results['mem_total_mb'] = args_mem[1]
    results['mem_used_mb'] = args_mem[2]
    results['mem_free_mb'] = args_mem[3]
    results['mem_shared_mb'] = args_mem[4]
    results['mem_buff_cache_mb'] = args_mem[5]
    results['mem_available_mb'] = args_mem[6]
    results['mem_swap_total_mb'] = args_mem_swap[1]
    results['mem_swap_used_mb'] = args_mem_swap[2]
    results['mem_swap_free_mb'] = args_mem_swap[3]
    return results


def get_info_net_dev(ssh: paramiko.SSHClient):
    results: dict = {}
    std_in, std_out, std_err = ssh.exec_command('cat /proc/net/dev')
    res, err = std_out.read(), std_err.read()
    result_net_dev = bytes.decode(res if res else err).strip()

    lines = re.sub(' +', ' ', result_net_dev).split('\n')
    # 删除 lo 本地回路网卡信息
    if lines[2][0: 2].strip() == 'lo':
        del lines[2]
    # 解析信息
    args = lines[2].strip().split(' ')
    results['net_receive_bytes'] = int(args[1].strip())
    results['net_receive_packets'] = int(args[2].strip())
    results['net_receive_errs'] = int(args[3].strip())
    results['net_receive_drop'] = int(args[4].strip())
    results['net_receive_fifo'] = int(args[5].strip())
    results['net_receive_frame'] = int(args[6].strip())
    results['net_receive_compressed'] = int(args[7].strip())
    results['net_receive_multicast'] = int(args[8].strip())
    results['net_transmit_bytes'] = int(args[9].strip())
    results['net_transmit_packets'] = int(args[10].strip())
    results['net_transmit_errs'] = int(args[11].strip())
    results['net_transmit_drop'] = int(args[12].strip())
    results['net_transmit_fifo'] = int(args[13].strip())
    results['net_transmit_colls'] = int(args[14].strip())
    results['net_transmit_carrier'] = int(args[15].strip())
    results['net_transmit_compressed'] = int(args[16].strip())
    return results


def get_info_disk_df(ssh: paramiko.SSHClient):
    results: dict = {}

    # 获取挂载盘路径
    std_in, std_out, std_err = ssh.exec_command('lsblk')
    res, err = std_out.read(), std_err.read()
    result_lsblk = bytes.decode(res if res else err).strip()
    args_mounted_path: list = []
    for line in result_lsblk.split('\n'):
        last = line.split(' ').pop().strip()
        if last[0: 1] == '/':
            args_mounted_path.append(last)

    # 统计挂载盘信息
    disk_all_mounted_total_kb = 0  # 磁盘总挂载大小
    disk_all_mounted_used_kb = 0  # 磁盘总使用大小
    disk_all_mounted_available_kb = 0  # 磁盘总可用大小
    result_disk_all_mounted: dict = {}
    for mounted_path in args_mounted_path:
        std_in, std_out, std_err = ssh.exec_command('df ' + mounted_path)
        res, err = std_out.read(), std_err.read()
        result_df = re.sub(' +', ' ', bytes.decode(res if res else err).strip())
        args = result_df.split('\n')[1].split(' ')
        result_disk_mounted: dict = {
            'disk_total_kb': int(args[1]),
            'disk_used_kb': int(args[2]),
            'disk_available_kb': int(args[3]),
            'disk_used_percent': int(args[4].replace('%', ''))
        }
        disk_all_mounted_total_kb += result_disk_mounted['disk_total_kb']
        disk_all_mounted_used_kb += result_disk_mounted['disk_used_kb']
        disk_all_mounted_available_kb += result_disk_mounted['disk_available_kb']
        result_disk_all_mounted[mounted_path] = result_disk_mounted
    # 磁盘挂载信息
    results['disk_all_mounted_total_kb'] = disk_all_mounted_total_kb
    results['disk_all_mounted_used_kb'] = disk_all_mounted_used_kb
    results['disk_all_mounted_available_kb'] = disk_all_mounted_available_kb
    results['disk_all_mounted_used_percent'] = int(disk_all_mounted_used_kb / disk_all_mounted_total_kb * 100)
    results['disk_detail'] = str(json.dumps(result_disk_all_mounted))

    return results


def get_info_top_cpu(ssh: paramiko.SSHClient):
    results: dict = {}
    std_in, std_out, std_err = ssh.exec_command('top -H -b -d 1 -n 10')
    res, err = std_out.read(), std_err.read()
    result_top_cpu = bytes.decode(res if res else err).strip()

    lines = re.sub(' +', ' ', result_top_cpu).split('\n')
    cpu_lines = []
    # 提取top命令中的多条CPU信息
    for line in lines:
        if len(line) > 8 and line[0: 8] == '%Cpu(s):':
            cpu_lines.append(line.strip())
    args_cpu_us = []  # 数组： 用户空间占用CPU百分比
    args_cpu_sy = []  # 数组： 内核空间占用CPU百分比
    args_cpu_ni = []  # 数组： 用户进程空间内改变过优先级的进程占用CPU百分比
    args_cpu_id = []  # 数组： 空闲CPU百分比
    args_cpu_wa = []  # 数组： 等待输入输出的CPU时间百分比
    args_cpu_hi = []  # 数组： 硬件CPU中断占用百分比
    args_cpu_si = []  # 数组： 软中断占用百分比
    args_cpu_st = []  # 数组： 虚拟机占用百分比
    for cpu_line in cpu_lines:
        args_cpu_info = cpu_line.split(',')
        args_cpu_us.append(float(args_cpu_info[0].strip().split(' ')[1]))
        args_cpu_sy.append(float(args_cpu_info[1].strip().split(' ')[0]))
        args_cpu_ni.append(float(args_cpu_info[2].strip().split(' ')[0]))
        args_cpu_id.append(float(args_cpu_info[3].strip().split(' ')[0]))
        args_cpu_wa.append(float(args_cpu_info[4].strip().split(' ')[0]))
        args_cpu_hi.append(float(args_cpu_info[5].strip().split(' ')[0]))
        args_cpu_si.append(float(args_cpu_info[6].strip().split(' ')[0]))
        args_cpu_st.append(float(args_cpu_info[7].strip().split(' ')[0]))
    """ 获取cpu各项信息的最大值、最小值、平均值 """
    # 用户空间占用CPU百分比
    results['cpu_us_max'] = max(args_cpu_us)
    results['cpu_us_min'] = min(args_cpu_us)
    results['cpu_us_avg'] = int(sum(args_cpu_us) / len(args_cpu_us) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 内核空间占用CPU百分比
    results['cpu_sy_max'] = max(args_cpu_sy)
    results['cpu_sy_min'] = min(args_cpu_sy)
    results['cpu_sy_avg'] = int(sum(args_cpu_sy) / len(args_cpu_sy) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 用户进程空间内改变过优先级的进程占用CPU百分比
    results['cpu_ni_max'] = max(args_cpu_ni)
    results['cpu_ni_min'] = min(args_cpu_ni)
    results['cpu_ni_avg'] = int(sum(args_cpu_ni) / len(args_cpu_ni) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 空闲CPU百分比
    results['cpu_id_max'] = max(args_cpu_id)
    results['cpu_id_min'] = min(args_cpu_id)
    results['cpu_id_avg'] = int(sum(args_cpu_id) / len(args_cpu_id) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 等待输入输出的CPU时间百分比
    results['cpu_wa_max'] = max(args_cpu_wa)
    results['cpu_wa_min'] = min(args_cpu_wa)
    results['cpu_wa_avg'] = int(sum(args_cpu_wa) / len(args_cpu_wa) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 硬件CPU中断占用百分比
    results['cpu_hi_max'] = max(args_cpu_hi)
    results['cpu_hi_min'] = min(args_cpu_hi)
    results['cpu_hi_avg'] = int(sum(args_cpu_hi) / len(args_cpu_hi) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 软中断占用百分比
    results['cpu_si_max'] = max(args_cpu_si)
    results['cpu_si_min'] = min(args_cpu_si)
    results['cpu_si_avg'] = int(sum(args_cpu_si) / len(args_cpu_si) * 100) / 100  # 乘100再除100，是为了处理float精度问题
    # 虚拟机占用百分比
    results['cpu_st_max'] = max(args_cpu_st)
    results['cpu_st_min'] = min(args_cpu_st)
    results['cpu_st_avg'] = int(sum(args_cpu_st) / len(args_cpu_st) * 100) / 100  # 乘100再除100，是为了处理float精度问题

    return results


def get_info_hostname(ssh: paramiko.SSHClient):
    results: dict = {}
    std_in, std_out, std_err = ssh.exec_command('hostname')
    res, err = std_out.read(), std_err.read()
    results['hostname'] = bytes.decode(res if res else err).strip()

    return results


def get_info(scan_dt: str, server: str, username: str = '', password: str = ''):
    """
    生产者： 服务器负载信息
    :param scan_dt: 扫描时间
    :param server: 服务器
    :param username: 用户名
    :param password: 密码
    :return: None
    """
    global data_of_server_loads
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    results: dict = {'scan_dt': scan_dt, 'server': server}

    try:
        """ 连接服务器 """
        if len(username.strip()) == 0:
            # private_key = paramiko.RSAKey.from_private_key_file('~/.ssh/id_rsa')
            ssh.connect(server, port=22)
        else:
            ssh.connect(hostname=server, port=22, username=username, password=password)

        """ 获取统计信息 """
        results = dict(get_info_hostname(ssh), **results)  # 主机名
        results = dict(get_info_uptime(ssh), **results)  # uptime信息
        results = dict(get_info_top_cpu(ssh), **results)  # top中的cpu信息
        results = dict(get_info_free_mb(ssh), **results)  # free -m 中的内存信息
        results = dict(get_info_net_dev(ssh), **results)  # 网卡负载信息
        results = dict(get_info_disk_df(ssh), **results)  # 磁盘负载

        results['is_succeed'] = 1
        results['remark'] = ''
        ssh.close()
    except Exception as e:
        results['is_succeed'] = 0
        results['remark'] = '获取服务器负载信息失败！' + str(e)
        logging.error('获取服务器[{0}]负载信息失败！{1}'.format(server, str(e)))
    finally:
        results['create_dt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_of_server_loads.put(results)


def save_data_to_db(data: dict):
    """
    保存数据到SQLite数据库中
    :param data: 数据
    :return:
    """
    if data['is_succeed'] == 1:
        sql = "insert into server_loads(                          \n " \
              "    scan_dt                                        \n " \
              "   ,server                                         \n " \
              "   ,is_succeed                                     \n " \
              "   ,create_dt                                      \n " \
              "   ,remark                                         \n " \
              "   ,disk_all_mounted_total_kb                      \n " \
              "   ,disk_all_mounted_used_kb                       \n " \
              "   ,disk_all_mounted_available_kb                  \n " \
              "   ,disk_all_mounted_used_percent                  \n " \
              "   ,disk_detail                                    \n " \
              "   ,net_receive_bytes                              \n " \
              "   ,net_receive_packets                            \n " \
              "   ,net_receive_errs                               \n " \
              "   ,net_receive_drop                               \n " \
              "   ,net_receive_fifo                               \n " \
              "   ,net_receive_frame                              \n " \
              "   ,net_receive_compressed                         \n " \
              "   ,net_receive_multicast                          \n " \
              "   ,net_transmit_bytes                             \n " \
              "   ,net_transmit_packets                           \n " \
              "   ,net_transmit_errs                              \n " \
              "   ,net_transmit_drop                              \n " \
              "   ,net_transmit_fifo                              \n " \
              "   ,net_transmit_colls                             \n " \
              "   ,net_transmit_carrier                           \n " \
              "   ,net_transmit_compressed                        \n " \
              "   ,mem_total_mb                                   \n " \
              "   ,mem_used_mb                                    \n " \
              "   ,mem_free_mb                                    \n " \
              "   ,mem_shared_mb                                  \n " \
              "   ,mem_buff_cache_mb                              \n " \
              "   ,mem_available_mb                               \n " \
              "   ,mem_swap_total_mb                              \n " \
              "   ,mem_swap_used_mb                               \n " \
              "   ,mem_swap_free_mb                               \n " \
              "   ,cpu_us_max                                     \n " \
              "   ,cpu_us_min                                     \n " \
              "   ,cpu_us_avg                                     \n " \
              "   ,cpu_sy_max                                     \n " \
              "   ,cpu_sy_min                                     \n " \
              "   ,cpu_sy_avg                                     \n " \
              "   ,cpu_ni_max                                     \n " \
              "   ,cpu_ni_min                                     \n " \
              "   ,cpu_ni_avg                                     \n " \
              "   ,cpu_id_max                                     \n " \
              "   ,cpu_id_min                                     \n " \
              "   ,cpu_id_avg                                     \n " \
              "   ,cpu_wa_max                                     \n " \
              "   ,cpu_wa_min                                     \n " \
              "   ,cpu_wa_avg                                     \n " \
              "   ,cpu_hi_max                                     \n " \
              "   ,cpu_hi_min                                     \n " \
              "   ,cpu_hi_avg                                     \n " \
              "   ,cpu_si_max                                     \n " \
              "   ,cpu_si_min                                     \n " \
              "   ,cpu_si_avg                                     \n " \
              "   ,cpu_st_max                                     \n " \
              "   ,cpu_st_min                                     \n " \
              "   ,cpu_st_avg                                     \n " \
              "   ,uptime_load_average_15min                      \n " \
              "   ,uptime_load_average_5min                       \n " \
              "   ,uptime_load_average_1min                       \n " \
              "   ,uptime_user_connections                        \n " \
              "   ,result_uptime_runtime                          \n " \
              "   ,hostname)                                      \n " \
              "values(                                            \n " \
              "    '{scan_dt}'                                    \n " \
              "   ,'{server}'                                     \n " \
              "   ,{is_succeed}                                   \n " \
              "   ,'{create_dt}'                                  \n " \
              "   ,'{remark}'                                     \n " \
              "   ,{disk_all_mounted_total_kb}                    \n " \
              "   ,{disk_all_mounted_used_kb}                     \n " \
              "   ,{disk_all_mounted_available_kb}                \n " \
              "   ,{disk_all_mounted_used_percent}                \n " \
              "   ,'{disk_detail}'                                \n " \
              "   ,{net_receive_bytes}                            \n " \
              "   ,{net_receive_packets}                          \n " \
              "   ,{net_receive_errs}                             \n " \
              "   ,{net_receive_drop}                             \n " \
              "   ,{net_receive_fifo}                             \n " \
              "   ,{net_receive_frame}                            \n " \
              "   ,{net_receive_compressed}                       \n " \
              "   ,{net_receive_multicast}                        \n " \
              "   ,{net_transmit_bytes}                           \n " \
              "   ,{net_transmit_packets}                         \n " \
              "   ,{net_transmit_errs}                            \n " \
              "   ,{net_transmit_drop}                            \n " \
              "   ,{net_transmit_fifo}                            \n " \
              "   ,{net_transmit_colls}                           \n " \
              "   ,{net_transmit_carrier}                         \n " \
              "   ,{net_transmit_compressed}                      \n " \
              "   ,{mem_total_mb}                                 \n " \
              "   ,{mem_used_mb}                                  \n " \
              "   ,{mem_free_mb}                                  \n " \
              "   ,{mem_shared_mb}                                \n " \
              "   ,{mem_buff_cache_mb}                            \n " \
              "   ,{mem_available_mb}                             \n " \
              "   ,{mem_swap_total_mb}                            \n " \
              "   ,{mem_swap_used_mb}                             \n " \
              "   ,{mem_swap_free_mb}                             \n " \
              "   ,{cpu_us_max}                                   \n " \
              "   ,{cpu_us_min}                                   \n " \
              "   ,{cpu_us_avg}                                   \n " \
              "   ,{cpu_sy_max}                                   \n " \
              "   ,{cpu_sy_min}                                   \n " \
              "   ,{cpu_sy_avg}                                   \n " \
              "   ,{cpu_ni_max}                                   \n " \
              "   ,{cpu_ni_min}                                   \n " \
              "   ,{cpu_ni_avg}                                   \n " \
              "   ,{cpu_id_max}                                   \n " \
              "   ,{cpu_id_min}                                   \n " \
              "   ,{cpu_id_avg}                                   \n " \
              "   ,{cpu_wa_max}                                   \n " \
              "   ,{cpu_wa_min}                                   \n " \
              "   ,{cpu_wa_avg}                                   \n " \
              "   ,{cpu_hi_max}                                   \n " \
              "   ,{cpu_hi_min}                                   \n " \
              "   ,{cpu_hi_avg}                                   \n " \
              "   ,{cpu_si_max}                                   \n " \
              "   ,{cpu_si_min}                                   \n " \
              "   ,{cpu_si_avg}                                   \n " \
              "   ,{cpu_st_max}                                   \n " \
              "   ,{cpu_st_min}                                   \n " \
              "   ,{cpu_st_avg}                                   \n " \
              "   ,{uptime_load_average_15min}                    \n " \
              "   ,{uptime_load_average_5min}                     \n " \
              "   ,{uptime_load_average_1min}                     \n " \
              "   ,{uptime_user_connections}                      \n " \
              "   ,'{result_uptime_runtime}'                      \n " \
              "   ,'{hostname}'                                   \n " \
              ");".format(scan_dt=data['scan_dt'],
                          server=data['server'],
                          is_succeed=data['is_succeed'],
                          create_dt=data['create_dt'],
                          remark=data['remark'],
                          disk_all_mounted_total_kb=data['disk_all_mounted_total_kb'],
                          disk_all_mounted_used_kb=data['disk_all_mounted_used_kb'],
                          disk_all_mounted_available_kb=data['disk_all_mounted_available_kb'],
                          disk_all_mounted_used_percent=data['disk_all_mounted_used_percent'],
                          disk_detail=data['disk_detail'],
                          net_receive_bytes=data['net_receive_bytes'],
                          net_receive_packets=data['net_receive_packets'],
                          net_receive_errs=data['net_receive_errs'],
                          net_receive_drop=data['net_receive_drop'],
                          net_receive_fifo=data['net_receive_fifo'],
                          net_receive_frame=data['net_receive_frame'],
                          net_receive_compressed=data['net_receive_compressed'],
                          net_receive_multicast=data['net_receive_multicast'],
                          net_transmit_bytes=data['net_transmit_bytes'],
                          net_transmit_packets=data['net_transmit_packets'],
                          net_transmit_errs=data['net_transmit_errs'],
                          net_transmit_drop=data['net_transmit_drop'],
                          net_transmit_fifo=data['net_transmit_fifo'],
                          net_transmit_colls=data['net_transmit_colls'],
                          net_transmit_carrier=data['net_transmit_carrier'],
                          net_transmit_compressed=data['net_transmit_compressed'],
                          mem_total_mb=data['mem_total_mb'],
                          mem_used_mb=data['mem_used_mb'],
                          mem_free_mb=data['mem_free_mb'],
                          mem_shared_mb=data['mem_shared_mb'],
                          mem_buff_cache_mb=data['mem_buff_cache_mb'],
                          mem_available_mb=data['mem_available_mb'],
                          mem_swap_total_mb=data['mem_swap_total_mb'],
                          mem_swap_used_mb=data['mem_swap_used_mb'],
                          mem_swap_free_mb=data['mem_swap_free_mb'],
                          cpu_us_max=data['cpu_us_max'],
                          cpu_us_min=data['cpu_us_min'],
                          cpu_us_avg=data['cpu_us_avg'],
                          cpu_sy_max=data['cpu_sy_max'],
                          cpu_sy_min=data['cpu_sy_min'],
                          cpu_sy_avg=data['cpu_sy_avg'],
                          cpu_ni_max=data['cpu_ni_max'],
                          cpu_ni_min=data['cpu_ni_min'],
                          cpu_ni_avg=data['cpu_ni_avg'],
                          cpu_id_max=data['cpu_id_max'],
                          cpu_id_min=data['cpu_id_min'],
                          cpu_id_avg=data['cpu_id_avg'],
                          cpu_wa_max=data['cpu_wa_max'],
                          cpu_wa_min=data['cpu_wa_min'],
                          cpu_wa_avg=data['cpu_wa_avg'],
                          cpu_hi_max=data['cpu_hi_max'],
                          cpu_hi_min=data['cpu_hi_min'],
                          cpu_hi_avg=data['cpu_hi_avg'],
                          cpu_si_max=data['cpu_si_max'],
                          cpu_si_min=data['cpu_si_min'],
                          cpu_si_avg=data['cpu_si_avg'],
                          cpu_st_max=data['cpu_st_max'],
                          cpu_st_min=data['cpu_st_min'],
                          cpu_st_avg=data['cpu_st_avg'],
                          uptime_load_average_15min=data['uptime_load_average_15min'],
                          uptime_load_average_5min=data['uptime_load_average_5min'],
                          uptime_load_average_1min=data['uptime_load_average_1min'],
                          uptime_user_connections=data['uptime_user_connections'],
                          result_uptime_runtime=data['result_uptime_runtime'],
                          hostname=data['hostname']
                          )
        do_sql(sql)

    # 服务器统计负载信息失败
    else:
        sql = "insert into server_loads(scan_dt, server, is_succeed, create_dt, remark)  " \
              "values('{scan_dt}', '{server}', {is_succeed}, '{create_dt}', '{remark}');" \
            .format(scan_dt=data['scan_dt'], server=data['server'],
                    is_succeed=data['is_succeed'], create_dt=data['create_dt'], remark=data['remark']
                    )
        do_sql(sql)


def stop_collect():
    """
    停止搜集服务器负载信息
    :return:
    """
    print('停止搜集功能未实现，请手动 kill 进程！')
    return True


def load_servers_from_file(filepath: str):
    """
    加载服务器列表
    :param filepath: 服务器列表配置文件路径
    :return:
    """
    try:
        with open(filepath, mode='rb') as file:
            sql = "delete from server_list; \n"
            server_list = []
            create_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            lines = file.read().decode().replace('\r', '\n').split('\n')
            for line in lines:
                args_line_info = line.strip().split(space_mark)
                args_line_info[0] = args_line_info[0].replace('\t', '').replace(' ', '')  # 服务器地址去空格
                server = args_line_info[0]
                username = args_line_info[1] if len(args_line_info) > 1 else ''
                password = args_line_info[2] if len(args_line_info) > 2 else ''
                if len(server) > 0:
                    sql += "insert into server_list(server, enable, username, password, create_dt) " \
                           "values('{0}', 1, '{1}', '{2}', '{3}'); \n" \
                        .format(server, username, password, create_dt)
                    server_list.append(server)
            do_multi_sql(sql)
            logging.info('导入文件[{0}]中的服务器列表成功！待扫描的服务器为：'.format(filepath) + ','.join(server_list))
            return True
    except Exception as e:
        logging.error('打开文件[{0}]失败： \n{1}'.format(filepath, str(e)))
        return False


if __name__ == '__main__':
    conn = sqlite3.connect(db_filename)
    # 初始化数据库表
    init_db_tables()

    # 判断传入参数，并做相应操作
    if len(sys.argv) == 1:
        print('脚本运行失败，运行输入参数个数为 0 ！')
        tip_for_input()
    elif str.lower(sys.argv[1]) == 'start':
        start_collect()
    elif str.lower(sys.argv[1]) == 'stop':
        stop_collect()
    elif str.lower(sys.argv[1]) == 'load_servers':
        if len(sys.argv) == 2:
            print('脚本运行失败，请输入服务器列表文件路径！')
        file_path = sys.argv[2]
        if os.path.exists(file_path) is False:
            print('脚本运行失败，服务器列表文件[{0}]不存在！'.format(file_path))
            exit(1)
        load_servers_from_file(file_path)
    else:
        print('脚本运行失败，输入参数错误！')
        tip_for_input()
