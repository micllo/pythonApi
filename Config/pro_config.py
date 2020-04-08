# -*- coding:utf-8 -*-


def get_pro_host(pro_name, host_name):
    """
    获取项目 HOST
    :param pro_name:
    :param host_name:
    :return:
    """
    if pro_name == "pro_demo_1":
        if host_name == "7060":
            return "http://127.0.0.1:7060/api_local"
    return None
