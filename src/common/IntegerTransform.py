def transform_int_from(value: str, base: int):
    """
    transform int string
    :param value: string like "b9"
    :param base: int like 90
    :return: int like 999
    """
    if base < 2 or base > 90:
        return None

    value = value.strip()

    base_str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%^&*()-_=+|;:,<.>/?`~[]{}"
    list_value = list(value)
    result_value = 0
    while len(list_value) > 0:
        result_value += base_str.find(list_value[0]) * (base ** (len(list_value) - 1))
        del list_value[0]
    return result_value


def transform_int_to(value: int, base: int):
    """
    transform int
    :param value: int like 999
    :param base: int like 90
    :return: string like "b9"
    """
    if base < 2 or base > 90:
        return None

    base_str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%^&*()-_=+|;:,<.>/?`~[]{}"
    list_value = []
    while value != 0:
        list_value.append(base_str[value % base])
        value = int(value / base)
    list_value.reverse()
    return "".join(list_value)
