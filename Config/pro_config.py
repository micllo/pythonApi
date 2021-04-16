# -*- coding:utf-8 -*-
import re
from Tools.mongodb import MongodbUtils
from Env import env_config as cfg
from Common.com_func import mongo_exception_send_DD

# 配置 项目对应的 HOST
# pro_host_dict = {}
# pro_demo_1_host = {"local": "http://127.0.0.1:7060/api_local",
#                    "docker": "http://192.168.31.9:1180/api",
#                    "google": "http://www.google.com.hk"}

# 配置 项目名称列表
pro_name_list = ["pro_demo_1", "google"]


# 通过项目名称从数据库中查出对应的host
#  {"pro_demo_1":["127.0.0.1", "192.168.31.9"], "pro_demo_2":["http://www.google.com.hk"]}
def get_pro_ip_dict():
    pro_host_dict = {}
    for pro_name in pro_name_list:
        server_list = []
        with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + "_host") as pro_db:
            try:
                for res in pro_db.find({}):
                    server_list.append(host_to_ip(res.get("host_url")))
            except Exception as e:
                print(e)
                mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目HOST有误")
                return "mongo error"
        pro_host_dict[pro_name] = server_list
    return pro_host_dict


def host_to_ip(host):
    """
    获取 host 中的 ip地址 或 域名
    :param host:
    :return:
    """
    match_obj = re.search(r'http://(.*?)/', host + "/")
    ip = match_obj.group(1)
    server_ip = ":" in ip and ip.split(":")[0] or ip
    return server_ip


def get_pro_name(test_url):
    """
    通过'测试地址'获取 项目名称、服务器IP
    （目的：监控负载均衡时，若某个服务器无响应，则需要定位该服务器地址）
    :param test_url:
    :return:
    """
    server_ip = host_to_ip(test_url)
    pro_name = ""
    for pro, server_list in get_pro_ip_dict().items():
        if server_ip in server_list:
            pro_name = pro
    return pro_name, server_ip


if __name__ == "__main__":
    print(get_pro_name("http://192.168.31.9:1180/api"))
    # print(get_pro_ip_dict())
