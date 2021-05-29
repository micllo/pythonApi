# coding:UTF-8
import pymongo
from Env import env_config_docker as cfg

"""
    【 Docker 项 目 配 置 】
    1.在 Docker 中启动新项目时，需要创建 xxxx_config 数据库
    2.为该数据库添加 添加 定时任务状态记录 
        {"config_type":"status", "config_name":"cron_status", "config_value": False}
"""


def create_collection(pro_name):

    # 创建mongo连接
    myclient = pymongo.MongoClient("mongodb://" + cfg.MONGODB_ADDR + "/")

    # 连接 数据库
    mydb = myclient[cfg.MONGODB_DATABASE]

    # 获取 集合（若不存在）
    mycoll = mydb[pro_name + "_config"]

    # 判断 config_name = cron_status 是否存在
    res = mycoll.find_one({"config_name": "cron_status"})
    if res:
        print(pro_name + "_config 表 存在 config_name = cron_status 记录")
    else:
        mycoll.insert_one({"config_type": "status", "config_name": "cron_status", "config_value": False})
        print(pro_name + "_config 表 新增 config_name = cron_status 记录成功！")


if __name__ == '__main__':

    create_collection("pro_demo_1")
