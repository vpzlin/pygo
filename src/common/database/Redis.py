###############################################################################
#  install library before use:                                                #
#      pip install redis                                                      #
###############################################################################


import redis


class Redis:
    def __init__(self):
        self.__db_redis: redis.ConnectionPool = None

    def __del__(self):
        self.__db_redis.disconnect()

    def connect_to_redis(self, host: str, port: int, password: str = None):
        """
        connect to redis database
        :param host: host ip or hostname
        :param port: host port
        :param password:
        """
        self.__db_redis = redis.Redis(host=host, port=port, password=password)
        return self.__db_redis

    def redis_get(self, key: str):
        value = self.__db_redis.get(key)
        if value is not None:
            value = value.decode()
        return value

    def redis_set(self, key: str, value: str):
        self.__db_redis.set(name=key, value=value)

    def redis_delete(self, key: str):
        self.__db_redis.delete(key)


