import logging


class Logging:
    def __init__(self):
        pass

    def __del__(self):
        pass

    def set_logging(self):
        """
        # logging levels
            CRITICAL  50
            ERROR     40
            WARNING   30
            INFO      20
            DEBUG     10
            NOTSET     0
        # format
            %(levelno)s     打印日志级别的数值
            %(levelname)s   打印日志级别名称
            %(pathname)s    打印当前执行程序的路径，其实就是sys.argv[0]
            %(filename)s    打印当前执行程序名
            %(funcName)s    打印日志的当前函数
            %(lineno)d      打印日志的当前行号
            %(asctime)s     打印日志的时间
            %(thread)d      打印线程ID
            %(threadName)s  打印线程名称
            %(process)d     打印进程ID
            %(message)s     打印日志信息
        """
        logging.basicConfig(format='%(asctime)s | %(levelname)s | %(filename)s line:%(lineno)d | %(message)s',
                            level=logging.DEBUG)
        pass
