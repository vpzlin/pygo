"""
#---------   before using this class   ---------#
# 1. Install library [thrift] for python
     pip install thrift

# 2. Install thrift
# 2.1. Install thrift on CentOS
      yum install thrift
# 2.2. Install thrift on Windows
#     Download [thrift-0.11.0.exe] of Windows' version on page url: http://thrift.apache.org/download

# 3. Generate packages by thrift
     cd hbase-1.3.1-src\hbase-thrift\src\main\resources\org\apache\hadoop\hbase\thrift
# 3.1. On CentOS
       thrift --gen py Hbase.thrift
# 3.2. On Windows
       thrift-0.11.0.exe --gen py Hbase.thrift
# 3.3. Copy generated files to the path of python library [thrift]
# 将生成的 gen-py目录下的 hbase目录 移动或复制到以下目录
       cp -r gen-py/hbase $PYTHON_HOME/Lib/site-packages/thrift/

4. Start service [thrift] on HBase, when it was started, new progress [ThriftServer] will appear
   sh $HBASE_HOME/bin/hbase-daemon.sh start thrift
"""

import pandas
import sys
import logging
from thrift.hbase.Hbase import *
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket


class HBaseByThrift:
    __client: Client
    __transport: TTransport

    def __init__(self, hbase_host: str, hbase_port: str,
                 hbase_transport: str = "buffered", hbase_protocol: str = "binary", timeout: str = "5000"):
        """
        init class of HBase using by thrift
        :param hbase_host: ip or hostname of hbase
        :param hbase_port: port of hbase
        :param transport: "buffered" or "framed", the first one is usual
        :param protocol: thrift only supports "binary"
        :param timeout: unit is MS
        """
        socket = TSocket.TSocket(hbase_host, hbase_port)

        # set transport
        hbase_transport = hbase_transport.strip().lower()
        if hbase_transport == "buffered":
            self.__transport = TTransport.TBufferedTransport(socket)
        elif hbase_transport == "framed":
            self.__transport = TTransport.TFramedTransport(socket)
        else:
            logging.error("Failed to init class [HBaseByThrift]! "
                          "Transport must be [binary] or [framed], but [{0}] was inputted.".format(hbase_transport))
            sys.exit(1)

        # set timeout
        socket.setTimeout(int(timeout))

        # set protocol
        hbase_protocol = hbase_protocol.strip().lower()
        if hbase_protocol == "binary":
            self.__protocol = TBinaryProtocol.TBinaryProtocol(self.__transport)
        else:
            logging.error("Failed to init class [HBaseByThrift]! "
                          "Protocol must be [protocol], but [{0}] was inputted.".format(hbase_protocol))
            sys.exit(1)

        # get client of HBase
        self.__client = Client(self.__protocol)
        self.__transport.open()
        logging.info("Connected to HBase server. Host = [{0}]. Port = [{1}]. Transport = [{2}]")

    def __del__(self):
        try:
            self.__transport.close()
            logging.info("Disconnected to HBase server.")
        except Exception as e:
            logging.debug("Failed to close transport of HBase. More info = [{0}]".format(str(e)))

    def enable_table(self, table_name: str):
        table_name = table_name.upper()
        try:
            self.__client.enableTable(table_name.encode())
            logging.info("Enabled table [{0}].".format(table_name))
            return True
        except Exception as e:
            logging.error("Failed to enable table [{0}]! More info = [{1}].".format(table_name, str(e)))
            return False

    def disable_table(self, table_name: str):
        table_name = table_name.strip().upper()
        try:
            self.__client.disableTable(table_name.encode())
            logging.info("Disabled table [{0}].".format(table_name))
            return 0
        except Exception as e:
            logging.error("Failed to disable table [{0}]! More info = [{1}].".format(table_name, str(e)))
            return 1

    def check_table_is_enabled(self, table_name: str):
        table_name = table_name.strip().upper()
        return self.__client.isTableEnabled(table_name.encode())

    def check_table_exists(self, table_name: str):
        table_name = table_name.strip().upper()
        for item in self.__client.getTableNames():
            if item.decode() == table_name.upper():
                return True
        return False

    def check_column_family_exist(self, table_name: str, column_family_name: str):
        table_name = table_name.strip().upper()
        column_family_name = column_family_name.strip().upper()
        for key, value in self.__client.getColumnDescriptors(table_name.encode()).items():
            if key.decode().upper() == column_family_name.upper() + ":":
                return True
        return False

    def get_all_table_names(self):
        table_names = []
        for item in self.__client.getTableNames():
            table_names.append(item.decode().upper())
        return table_names

    def create_table(self, table_name: str, column_family_names: list, max_versions: int = 5):
        table_name = table_name.upper()
        # 将 column family names 由字符型转为 HBase column 数组
        column_families = []
        for column_family_name in column_family_names:
            column_family = ColumnDescriptor()
            column_family.name = (str(column_family_name).upper() + ":").encode()
            column_family.maxVersions = max_versions
            column_families.append(column_family)
        # 创建表
        try:
            self.__client.createTable(table_name.encode(), column_families)
            logging.info("Created HBase table [{0}], column family names = [{1}]."
                         .format(table_name, column_family_names))
            return 0
        except Exception as e:
            logging.error("Failed in creating HBase table [{0}]! Column family names = [{1}]. More error info = [{2}]"
                          .format(table_name, column_family_names, str(e)))
            return 1

    def drop_table(self, table_name: str):
        table_name = table_name.strip().upper()
        if self.check_table_exists(table_name) is False:
            logging.error("Failed to drop table [{0}]! This table doesn't exist.".format(table_name))
            return False
        # firstly, disable HBase table
        try:
            self.__client.disableTable(table_name.encode())
            logging.info("Disabled HBase table [{0}]".format(table_name))
        except Exception as e:
            logging.error("Failed to disable HBase table [{0}]! More info = [{1}]".format(table_name, str(e)))
            return False
        # secondly, drop HBase table
        try:
            self.__client.deleteTable(table_name.encode())
            logging.info("Dropped HBase table [{0}].".format(table_name))
            return True
        except Exception as e:
            logging.error("Failed to drop HBase table [{0}]. More info = [{1}]".format(table_name, str(e)))
            return False

