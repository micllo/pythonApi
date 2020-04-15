# -*-coding: utf-8 -*-
import traceback
from pymongo import MongoClient
from pymongo import ReadPreference
from pymongo.write_concern import WriteConcern
from Env import env_config as cfg
from Common.com_func import log

db_pool = {}


class MongodbUtils(object):
    """
    此类用于链接mongodb数据库
    write_concern='majority'：表示所有节点写入成功后，才算成功
    write_concern=2： 表示只需要两个节点写入成功后，即为成功
    """
    def __init__(self, collection="", ip="", port=None, database="",
                 replica_set_name="", read_preference=ReadPreference.SECONDARY_PREFERRED,
                 write_concern="majority"):

        self.collection = collection
        self.ip = ip
        self.port = port
        self.database = database
        self.replica_set_name = replica_set_name
        self.read_preference = read_preference
        self.write_concern = write_concern

        if (ip, port) not in db_pool:
            db_pool[(ip, port)] = self.db_connection()
        elif not db_pool[(ip, port)]:
            db_pool[(ip, port)] = self.db_connection()

        self.db = db_pool[(ip, port)]
        self.db_table = self.db_table_connect()

    def __enter__(self):
        return self.db_table

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def db_connection(self):
        db = None
        try:
            if self.replica_set_name:
                # 当pymongo更新到3.x版本, 连接副本集的方法得用MongoClient, 如果版本<=2.8.1的, 得用MongoReplicaSetClient
                db = MongoClient(self.ip, replicaset=self.replica_set_name)
            else:
                db = MongoClient(self.ip, self.port)
            log.info("mongodb connection success")

        except Exception as e:
            log.error("mongodb connection failed: %s" % self.collection)
            print(e)
            print(traceback.format_exc())
        return db

    def db_table_connect(self):
        db = self.db.get_database(self.database, read_preference=self.read_preference,
                                  write_concern=WriteConcern(w=self.write_concern))
        table_db = db[self.collection]
        return table_db


if __name__ == '__main__':

    # with MongodbUtils(ip=cfg.MONGODB_IP_PORT, database="monitorAPI", collection="monitorResult") as monitor_db:
    #     res = monitor_db.find_one({"testCaseName": "获取图片验证码_200_MONITOR"}, {"_id": 0})
    #     print(res)
    #     print(monitor_db)

    img_file_full = cfg.SCREENSHOTS_PATH + "TrainTest/test_ctrip/search_train_1.png"
    # mgf.upload_file(img_file_full)
    mgf.get_base64_by_id("5e61152ff0dd77751382563f")
    # mgf.download_file_by_name("search_train_3", "/Users/micllo/Downloads/test2.png")
