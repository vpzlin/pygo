from datetime import datetime
import uuid


def get_current_date_len8():
    """
    :return: yyyymmdd
    """
    date_current = datetime.now().strftime("%Y%m%d")
    return date_current


def get_current_date_len10():
    """
    :return: yyyy-mm-dd
    """
    date_current = datetime.now().strftime("%Y-%m-%d")
    return date_current


def get_current_year_len4():
    """
    :return: yyyy
    """
    year_current = datetime.now().strftime("%Y")
    return year_current


def get_current_year_month_len6():
    """
    :return: yyyymm
    """
    year_month_current = datetime.now().strftime("%Y%m")
    return year_month_current


def get_current_year_month_len7():
    """
    :return: yyyymm
    """
    year_month_current = datetime.now().strftime("%Y-%m")
    return year_month_current


def get_current_datetime_len23():
    """
    :return: yyyy-mm-dd HH:MM:SS.sss
    """
    datetime_current = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    datetime_current = datetime_current[0: -3]
    return datetime_current


def get_current_datetime_len17():
    """
    :return: yyyymmddHHMMSSsss
    """
    datetime_current = datetime.now().strftime("%Y%m%d%H%M%S%f")
    datetime_current = datetime_current[0: -3]
    return datetime_current


def get_uuid_len32():
    """
    :return: uuid with length 32, base on MAC and timestamp
    """
    uuid_current = uuid.uuid1()
    return str(uuid_current).replace("-", "")


def get_uuid_len36():
    """
    :return: uuid with length 36, base on MAC and timestamp
    """
    uuid_current = uuid.uuid1()
    return str(uuid_current)


def get_current_timestamp_len10():
    """
    :return:
    """
    return int(datetime.timestamp(datetime.now()))
