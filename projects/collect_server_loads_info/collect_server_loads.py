import sys
import os
import sqlite3
import threading
import paramiko
import time
from datetime import datetime


"""
set parameters
"""
conn: sqlite3.Connection                # sqlite数据库连接
scan_interval_seconds = 1000              # 扫描间隔（单位:秒）
db_filename = 'server_loads_info.db'    # sqlite数据文件


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
    # 创建表
    do_multi_sql('create table if not exists server_list(  -- 表:服务器列表      \n'
                 '    server     varchar(19)               -- 服务器IP或服务器名  \n'
                 '   ,enable     int                       -- 是否可用:0否,1是   \n'
                 '   ,username   varchar(20)               -- 是否可用:0否,1是   \n'
                 '   ,password   varchar(100)              -- 是否可用:0否,1是   \n'
                 '   ,create_dt  date                      -- 记录创建时间       \n'
                 '   ,remark     varchar(400)              -- 备注              \n'
                 '   ,primary key(server)                                      \n'
                 ')')
    do_multi_sql('create table if not exists server_loads(          -- 表:服务器负载                 \n'
                 '    scan_dt                     varchar(19)       -- 扫描时间                     \n'
                 '   ,server                      varchar(100)      -- 服务器IP或服务器名             \n'
                 '   ,is_succeed                  int               -- 是否扫描成功:1为成功,0为失败    \n'
                 '   ,uptime_runtime              varchar(100)      -- 系统运行时间                  \n'
                 '   ,uptime_user_connections     int               -- 用户总连接数                  \n'
                 '   ,uptime_load_average_1min    int               -- 系统平均负载（最近1分钟）       \n'
                 '   ,uptime_load_average_5min    int               -- 系统平均负载（最近5分钟）       \n'
                 '   ,uptime_load_average_15min   int               -- 系统平均负载（最近15分钟）      \n'
                 '   ,is_succeed                  int               -- 是否扫描成功:1为成功,0为失败    \n'
                 '   ,cpu_load                    real              -- CPU负载（%）                 \n'
                 '   ,mem_total_mb                int               -- 总物理内存(MB)               \n'
                 '   ,mem_used_mb                 int               -- 已使用物理内存(MB)            \n'
                 '   ,mem_free_mb                 int               -- 未使用物理内存(MB)            \n'
                 '   ,mem_shared_mb               int               -- 多进程共享内存(MB)            \n'
                 '   ,mem_buffer_cache_mb         int               -- 读写缓存内存(MB)              \n'
                 '   ,mem_available_mb            int               -- 可被应用程序使用的物理内存(MB)  \n'
                 '   ,create_dt                   date              -- 记录创建时间                 \n'
                 '   ,remark                      varchar(400)      -- 备注                        \n'
                 '   ,primary key(scan_dt, server)'
                 ')')
    print("初始化SQLite数据库文件[{0}]完毕。\n".format(db_filename))


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
        # 获取待查负载的服务器
        results = do_sql("select server, username, password from server_list where enable = 1")
        scan_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for server, username, password in results:
            print('开始搜集服务器[{0}]的负载。'.format(server))
            t = threading.Thread(target=collect_info, args=(scan_dt, server, username, password))
            t.start()
        # 进程休眠
        print('进程休眠 {0}秒'.format(scan_interval_seconds))
        time.sleep(scan_interval_seconds)

    #

    return True


def get_info_uptime(result_uptime: str):
    """
    解析uptime命令的字符串
    :param result_uptime:
    :return:
    """
    results: dict = {}
    args = result_uptime.split(',')
    results['uptime_load_average_15min'] = args.pop()
    results['uptime_load_average_5min'] = args.pop()
    results['uptime_load_average_1min'] = args.pop().split(' ').pop()
    results['uptime_user_connections'] = args.pop().strip().split(' ')[0]
    args1 = args[0].split(' ')
    del args1[0]    # 删除当前时间
    del args1[0]    # 删除'up'字符串
    args[0] = ' '.join(args1)
    args[1] = args[1].strip()
    results['result_uptime_runtime'] = ' '.join(args)
    return results


def get_info_free_mb(result_free_mb):
    results: dict = {}
    lines = result_free_mb.split('\n')
    args_mem = lines[1].split(' ')
    args_mem_swap = lines[2].split(' ')
    results['mem_total_mb']      = args_mem[1]
    results['mem_used_mb']       = args_mem[2]
    results['mem_free_mb']       = args_mem[3]
    results['mem_shared_mb']     = args_mem[4]
    results['mem_buff_cache_mb'] = args_mem[5]
    results['mem_available_mb']  = args_mem[6]
    results['mem_swap_total_mb'] = args_mem_swap[1]
    results['mem_swap_used_mb']  = args_mem_swap[2]
    results['mem_swap_free_mb']  = args_mem_swap[3]
    return results


def get_info_net_dev(result_net_dev):
    results: dict = {}
    lines = result_net_dev.split('\n')
    # 删除 lo 本地回路网卡信息
    if lines[2][0: 2].strip() == 'lo':
        del lines[2]
    # 解析信息
    args = lines[2].split(' ')
    results['net_receive_bytes']       = int(args[1].strip())
    results['net_receive_packets']     = int(args[2].strip())
    results['net_receive_errs']        = int(args[3].strip())
    results['net_receive_drop']        = int(args[4].strip())
    results['net_receive_fifo']        = int(args[5].strip())
    results['net_receive_frame']       = int(args[6].strip())
    results['net_receive_compressed']  = int(args[7].strip())
    results['net_receive_multicast']   = int(args[8].strip())
    results['net_transmit_bytes']      = int(args[9].strip())
    results['net_transmit_packets']    = int(args[10].strip())
    results['net_transmit_errs']       = int(args[11].strip())
    results['net_transmit_drop']       = int(args[12].strip())
    results['net_transmit_fifo']       = int(args[13].strip())
    results['net_transmit_colls']      = int(args[14].strip())
    results['net_transmit_carrier']    = int(args[15].strip())
    results['net_transmit_compressed'] = int(args[16].strip())
    return results


def collect_info(scan_dt: str, server: str, username: str = '', password: str = ''):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    create_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    try:
        results: dict = {}
        """ 连接服务器 """
        if len(username.strip()) == 0:
            # private_key = paramiko.RSAKey.from_private_key_file('~/.ssh/id_rsa')
            ssh.connect(server, port=22)
        else:
            ssh.connect(hostname=server, port=22, username=username, password=password)

        """ 获取系统负载信息 """
        std_in, std_out, std_err = ssh.exec_command('uptime')
        res, err = std_out.read(), std_err.read()
        result_uptime = bytes.decode(res if res else err).strip()
        results = dict(get_info_uptime(result_uptime), **results)

        """ 获取内存负载信息 """
        std_in, std_out, std_err = ssh.exec_command('free -m')
        res, err = std_out.read(), std_err.read()
        result_free_mb = bytes.decode(res if res else err).strip()
        results = dict(get_info_free_mb(result_free_mb), **results)

        """ 获取网卡负载信息 """
        std_in, std_out, std_err = ssh.exec_command('cat /proc/net/dev')
        res, err = std_out.read(), std_err.read()
        result_net_dev = bytes.decode(res if res else err).strip()
        results = dict(get_info_net_dev(result_net_dev), **results)

        """ 获取磁盘负载信息 """



        """ 断开连接服务器 """
        ssh.close()

        # 插入负载数据
        sql = "insert into server_loads(    \n" \
              "    scan_dt                  \n" \
              "   ,server                   \n" \
              "   ,is_succeed               \n" \
              "   ,cpu_load                 \n" \
              "   ,mem_total_mb             \n" \
              "   ,mem_used_mb              \n" \
              "   ,mem_free_mb              \n" \
              "   ,mem_shared_mb            \n" \
              "   ,mem_buffer_cache_mb      \n" \
              "   ,mem_available_mb         \n" \
              "   ,create_dt                \n" \
              "   ,remark                   \n" \
              ") values('{0}', '1', 1, null, null, null, null, null, null, null, {2}， {3});" \
            .format(scan_dt, server, create_dt, '获取负载信息失败：')
        #do_sql(sql)
    except Exception as e:
        sql = "insert into server_loads(    \n" \
              "    scan_dt                  \n" \
              "   ,server                   \n" \
              "   ,is_succeed               \n" \
              "   ,cpu_load                 \n" \
              "   ,mem_total_mb             \n" \
              "   ,mem_used_mb              \n" \
              "   ,mem_free_mb              \n" \
              "   ,mem_shared_mb            \n" \
              "   ,mem_buffer_cache_mb      \n" \
              "   ,mem_available_mb         \n" \
              "   ,create_dt                \n" \
              "   ,remark                   \n" \
              ") values('{0}', '1', 0, null, null, null, null, null, null, null, {2}， {3});"\
            .format(scan_dt, server, create_dt, '获取负载信息失败：' + str(e))
        #do_sql(sql)


def stop_collect():
    """
    停止搜集服务器负载信息
    :return:
    """
    print('停止搜集功能未实现，请手动停止进程！')
    return True


def load_servers(filepath: str, file_encoding: str = 'UTF-8'):
    """
    加载服务器列表
    :param filepath: 服务器列表配置文件路径
    :param file_encoding:  文件编码
    :return:
    """
    try:
        with open(filepath, 'r', encoding=file_encoding) as file:
            sql = "delete from server_list; \n"
            server_list = []
            create_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            for line in file.readlines():
                line_info = line.strip().replace('\t', ' ').split(' ')
                server = line_info[0]
                username = line_info[1] if len(line_info) > 1 else ''
                password = line_info[2] if len(line_info) > 2 else ''
                if len(server) > 0:
                    sql += "insert into server_list(server, enable, username, password, create_dt) " \
                           "values('{0}', 1, '{1}', '{2}', '{3}'); \n" \
                        .format(server, username, password, create_dt)
                    server_list.append(server)
            do_multi_sql(sql)
            print('导入文件[{0}]中的服务器列表成功！待扫描的服务器为：'.format(filepath) + ','.join(server_list))
            return True
    except Exception as e:
        print('打开文件[{0}]失败： \n{1}'.format(filepath, str(e)))
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
        load_servers(file_path)
    else:
        print('脚本运行失败，输入参数错误！')
        tip_for_input()
