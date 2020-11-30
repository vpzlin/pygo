import sys
import os
import sqlite3
import threading
from datetime import datetime


"""
set parameters
"""
conn: sqlite3.Connection  # sqlite数据库连接
scan_interval_seconds = 60  # 扫描间隔（单位:秒）
db_filename = 'server_loads_info.db'  # sqlite数据文件
servers_filename = 'servers.txt'  # 服务器列表


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
                 '   ,is_usable  varchar(19)               -- 是否可用:0否,1是   \n'
                 '   ,create_dt  date                      -- 创建日期与时间      \n'
                 '   ,remark     varchar(400)              -- 备注              \n'
                 '   ,primary key(server)                                      \n'
                 ')')
    do_multi_sql('create table if not exists server_loads(    -- 表:服务器负载                 \n'
                 '    scan_dt               varchar(19)       -- 扫描时间                     \n'
                 '   ,server                varchar(100)      -- 服务器IP或服务器名             \n'
                 '   ,is_succeed            int               -- 是否扫描成功:1为成功,0为失败    \n'
                 '   ,cpu_load              real              -- CPU负载（%）                 \n'
                 '   ,mem_total_mb          int               -- 总物理内存(MB)               \n'
                 '   ,mem_used_mb           int               -- 已使用物理内存(MB)            \n'
                 '   ,mem_free_mb           int               -- 未使用物理内存(MB)            \n'
                 '   ,mem_shared_mb         int               -- 多进程共享内存(MB)            \n'
                 '   ,mem_buffer_cache_mb   int               -- 读写缓存内存(MB)              \n'
                 '   ,mem_available_mb      int               -- 可被应用程序使用的物理内存(MB)  \n'
                 '   ,remark                varchar(400)      -- 备注                        \n'
                 '   ,primary key(scan_dt, server)'
                 ')')
    print("初始化SQLite数据库文件[{0}]成功。\n".format(db_filename))


def tip_for_input():
    """
    输入参数提示
    :return: 
    """
    tip = '    运行方法： python3 {0} start | stop | load_servers server_list_file    \n' \
          '    参数说明： start                      -->  启动脚本                     \n' \
          '             stop                       -->  停止脚本                     \n' \
          '             load_servers server_list_file  -->  载入服务器列表文件'.format(sys.argv[0])
    print(tip)


def start_collect():
    """
    开始搜集服务器负载信息
    :return:
    """
    # 获取待查负载的服务器
    results = do_sql("select server, is_usable from server_list where is_usable = 1")
    for server, is_usable in results:
        t = threading.Thread(target=collect_info, args=(server,))

    #

    return True


def collect_info(server: str, port: int = 22, username: str = 'root'):
    results: dict = []

    return results


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
            sql = ""
            server_list = []
            create_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            for line in file.readlines():
                server = line.strip()
                if len(server) > 0:
                    sql += "insert into server_list(server, is_usable, create_dt) values('{0}', 1, '{1}');\n" \
                        .format(server, create_dt)
                    server_list.append(server)
            do_sql(sql)
            print('导入文件[{0}]中的服务器列表成功！服务器：'.format(filepath) + ','.join(server_list))
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
