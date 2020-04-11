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
        if host_name == "1111":
            host = "http://www.google.com.hk/api_local"
    return host


def get_pro_name(test_url):
    """
    通过 测试地址 获取 项目名称
    :param test_url:
    :return:
    """
    pro_name = None
    if "127.0.0.1:7060" in test_url:
        pro_name = "pro_demo_1"
    elif "www.google.com.hk" in test_url:
        pro_name = "谷歌"
    return pro_name



