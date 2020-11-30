"""
[library requires]
    [cx_oracle] ---- deal with oracle
        [install]       pip install cx_oracle
        [document]      https://oracle.github.io/python-cx_Oracle/
                        http://cx-oracle.readthedocs.io/en/latest/

[update logs]
    20180815 - Init.
"""
import logging
import pandas as pd
import cx_Oracle


class Oracle:
    def __init__(self, p_host: str, p_port: str, p_service_name: str, p_username: str, p_password: str):
        self.connection = self.connect_oracle(p_host, p_port, p_service_name, p_username, p_password)

    def __del__(self):
        self.disconnect_oracle()

    def connect_oracle(self, p_host: str, p_port: str, p_service_name: str, p_username: str, p_password: str):
        p_host = p_host.strip()
        p_port = p_port.strip()
        p_service_name = p_service_name.strip()
        p_username = p_username.strip()
        p_password = p_password.strip()
        try:
            connection = cx_Oracle.connect(
                "{0}/{1}@{2}:{3}/{4}".format(p_username, p_password, p_host, p_port, p_service_name))
            logging.debug("Connected to database on Oracle, host = [{0}], username = [{1}], database = [{2}]."
                          .format(p_host, p_username, p_service_name))
            return connection
        except Exception as ex:
            logging.error("Failed to connect Oracle!"
                          "\nMore info = [{0}]".format(str(ex)))
            return None

    def disconnect_oracle(self):
        try:
            if self.connection:
                self.connection.close()
            logging.debug("Disconnected database Oracle.")
        except Exception as ex:
            logging.error(str(ex))

    def commit(self):
        try:
            self.connection.commit()
        except Exception as ex:
            logging.error("Failed to commit! More info = [{0}].".format(str(ex)))

    def get_cursor(self):
        try:
            return self.connection.cursor()
        except Exception as ex:
            logging.error("Failed to get cursor! More info = [{0}].".format(str(ex)))
            return None

    def do_sql(self, sql: str, p_commit: bool = False):
        sql = sql.strip()
        str_sql_start = sql[: sql.find(" ")].lower()
        # when select, return results
        if str_sql_start == "select":
            return self.__do_select(sql, p_commit)
        else:
            cursor = self.get_cursor()
            try:
                cursor.execute(sql)
                if p_commit is True:
                    self.connection.commit()
            except Exception as ex:
                logging.error("Failed to execute SQL."
                              "\nSQL = [{0}]"
                              "\nMore info = [{1}]"
                              .format(sql, str(ex)))
                return None
            finally:
                cursor.close()

    def __do_select(self, sql: str, p_commit: bool = False):
        """
        query: select
            :param sql: SQL to be executed
            :param p_commit: commit flag
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
                # get column names and transform to upper
                column_names = []
                for column in cursor.description:
                    column_names.append(column[0].upper())
                df_result.columns = column_names
                return df_result
        except Exception as ex:
            logging.error("Failed to execute SQL."
                          "\nSQL = [{0}]"
                          "\nMore info = [{1}]"
                          .format(sql, str(ex)))
            return None
        finally:
            cursor.close()


