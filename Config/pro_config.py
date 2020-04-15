# -*- coding:utf-8 -*-
import re

# 配置 项目对应的 HOST
pro_demo_1_host = {"local": "http://127.0.0.1:7060/api_local",
                   "docker": "http://192.168.31.10:1180/api",
                   "1111": "http://www.google.com.hk"}

pro_host_dict = {}
pro_host_dict["pro_demo_1"] = pro_demo_1_host

# 配置 项目对应的服务器地址（目的：监控负载均衡时，若某个服务器无响应，则需要定位该服务器地址）
pro_server_dict = {}
pro_server_dict["pro_demo_1"] = ["127.0.0.1", "192.168.31.10"]
pro_server_dict["google"] = ["www.google.com.hk"]


def get_pro_host(pro_name, host_name):
    """
    获取项目HOST
    :param pro_name:
    :param host_name:
    :return:
    """
    host = None
    for name, pro_dict in pro_host_dict.items():
        if pro_name == name:
            host = pro_dict.get(host_name, None)
    return host


def get_pro_name(test_url):
    """
    通过'测试地址'获取 项目名称、服务器IP
    （目的：监控负载均衡时，若某个服务器无响应，则需要定位该服务器地址）
    :param test_url:
    :return:
    """
    match_obj = re.search(r'http://(.*?)/', test_url + "/")
    ip = match_obj.group(1)
    server_ip = ":" in ip and ip.split(":")[0] or ip
    pro_name = ""
    for name, server_list in pro_server_dict.items():
        if server_ip in server_list:
            pro_name = name
    return pro_name, server_ip


if __name__ == "__main__":
    get_pro_name("http://192.168.31.10:1180/api")
    # get_pro_name("http://www.google.com.hk")