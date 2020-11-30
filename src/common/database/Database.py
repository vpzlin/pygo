"""
[library requires]
    [pymysql] ---- deal with mysql
        [download page] https://pypi.org/project/PyMySQL/#files
        [download file] PyMySQL-0.8.1-py2.py3-none-any.whl
        [document]      https://pymysql.readthedocs.io/en/latest/index.html
        [install]       pip install PyMySQL-0.8.1-py2.py3-none-any.whl
    [cx_oracle] ---- deal with oracle
        [install]       pip install cx_oracle
        [document]      https://oracle.github.io/python-cx_Oracle/
                        http://cx-oracle.readthedocs.io/en/latest/

[update logs]
    20180518 - Init
"""

import logging
import sys
import pandas as pd
import pymysql
import cx_Oracle


class Database:
    def __init__(self, p_database: str):
        """
        init class
        :param p_database: type of database, supports [mysql], [oracle], [sqlite]
        """
        # init functions according to database type
        database = p_database.strip().lower()
        if database == "mysql":
            self.connect_database = self.__connect_mysql
            self.disconnect_database = self.__disconnect_mysql
            self.get_cursor = self.__get_cursor_mysql
            self.do_sql = self.__do_sql_mysql
            self.commit = self.__commit_mysql
        elif database == "oracle":
            self.connect_database = self.__connect_oracle
            self.disconnect_database = self.__disconnect_oracle
            self.get_cursor = self.__get_cursor_oracle
            self.do_sql = self.__do_sql_oracle
            self.commit = self.__commit_oracle
        elif database == "sqlite":
            self.connect_database = self.__connect_sqlite
            self.disconnect_database = self.__disconnect_sqlite
            self.get_cursor = self.__get_cursor_sqlite
            self.do_sql = self.__do_sql_sqlite
            self.commit = self.__commit_sqlite
        else:
            logging.error("Wrong database type [{0}] is inputted."
                          "\nCurrent supports are only mysql, oracle or sqlite!"
                          .format(p_database))
            logging.info("Program exited.")
            sys.exit(1)
        pass

    def __del__(self):
        self.disconnect_database()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    connect database
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __connect_mysql(self, p_host: str, p_username: str, p_password: str, p_db_name: str,
                        p_charset: str = 'utf8mb4'):
        """
        get connection to mysql
        :param p_host: hostname or ip
        :param p_username: mysql username
        :param p_password: password for mysql username
        :param p_db_name: mysql database name
        :param p_charset: charset of the mysql database
        :return:
        """
        p_host = p_host.strip()
        p_username = p_username.strip()
        p_password = p_password.strip()
        p_db_name = p_db_name.strip()
        p_charset = p_charset.strip()
        try:
            self.connection = pymysql.connect(host=p_host, user=p_username, password=p_password, db=p_db_name,
                                              charset=p_charset, cursorclass=pymysql.cursors.DictCursor)
            logging.debug("Connected to database on MySQL, host = [{0}], username = [{1}], database = [{2}]."
                          .format(p_host, p_username, p_db_name))
        except Exception as e:
            logging.error("Failed to connect MySQL!"
                          "\nMore info = [{0}]".format(str(e)))
            return None

    def __connect_oracle(self, p_username: str, p_password: str, p_host: str, p_port: str, p_service_name: str):
        """
        get connection to oracle
        :param p_host: hostname or ip
        :param p_port: oracle database port
        :param p_username: oracle username
        :param p_password: password for oracle username
        :param p_db_name: oracle database name
        :return:
        """
        p_username = p_username.strip()
        p_password = p_password.strip()
        p_host = p_host.strip()
        p_port = p_port.strip()
        p_service_name = p_service_name.strip()
        try:
            self.connection = cx_Oracle.connect("{0}/{1}@{2}:{3}/{4}".format(p_username, p_password, p_host, p_port, p_service_name))
            logging.debug("Connected to database on Oracle, host = [{0}], username = [{1}], database = [{2}]."
                          .format(p_host, p_username, p_service_name))
        except Exception as e:
            logging.error("Failed to connect Oracle!"
                          "\nMore info = [{0}]".format(str(e)))
            return None

    def __connect_sqlite(self):
        pass

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    disconnect database
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    def __disconnect_mysql(self):
        """
        release connection, it'll auto run when class is over.
        :return: None
        """
        try:
            if self.connection:
                self.connection.close()
                logging.debug("Disconnected database MySQL.")
        except Exception as e:
            logging.error(str(e))

    def __disconnect_oracle(self):
        try:
            if self.connection:
                self.connection.close()
            logging.debug("Disconnected database Oracle.")
        except Exception as e:
            logging.error(str(e))

    def __disconnect_sqlite(self):
        pass

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    get cursor
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __get_cursor_mysql(self):
        return self.connection.cursor()

    def __get_cursor_oracle(self):
        return self.connection.cursor()

    def __get_cursor_sqlite(self):
        pass

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    commit
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __commit_mysql(self):
        self.connection.commit()

    def __commit_oracle(self):
        self.connection.commit()

    def __commit_sqlite(self):
        self.connection.commit()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    do sql
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __do_sql_mysql(self, sql: str, p_commit: bool = True):
        """
        do sql: select,update,delete...and so on
        :param sql: SQL to be executed
        :return: None ---> when failed to execute SQL
                  pandas dataframe ---> query results, field names trans to upper
        """
        cursor = self.get_cursor()
        try:
            cursor.execute(sql)
            if p_commit is True:
                self.connection.commit()

            # fetch query result if possible
            result = cursor.fetchall()
            if result:
                df_result = pd.DataFrame(result)
                # upper the column names
                df_result.columns = df_result.columns.str.upper()
                return df_result
        except Exception as e:
            logging.error("Failed to execute SQL."
                          "\nSQL = [{0}]"
                          "\nMore info = [{1}]"
                          .format(sql, str(e)))
            return None
        finally:
            cursor.close()

    def __do_sql_oracle(self, sql: str, p_commit: bool = True):
        """
        do sql: select,update,delete...and so on
        :param sql: SQL to be executed
        :return: None ---> when failed to execute SQL
                  pandas dataframe ---> query results, field names trans to upper
        """
        cursor = self.get_cursor()
        try:
            cursor.prepare(sql)
            cursor.execute()
            if p_commit is True:
                self.connection.commit()
        except Exception as e:
            logging.error("Failed to execute SQL."
                          "\nSQL = [{0}]"
                          "\nMore info = [{1}]"
                          .format(sql, str(e)))
            return None
        finally:
            cursor.close()

    def __do_sql_sqlite(self, sql: str, p_commit: bool = True):
        pass
