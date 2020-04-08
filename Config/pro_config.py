# -*- coding:utf-8 -*-
from Common.com_func import log


def get_pro_host(pro_name, host_name):
    """
    获取项目HOST
    :param pro_name:
    :param host_name:
    :return:
    """
    host = None
    if pro_name == "pro_demo_1":
        if host_name == "7060":
            host = "http://127.0.0.1:7060/api_local"
    return host


