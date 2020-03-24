# -*- coding:utf-8 -*-
from Config import config as cfg
from Common.com_func import log, is_null
import sys, os, time
from Tools.mongodb import MongodbUtils
from dateutil import parser
import unittest

# sys.path.append("./")


"""
api 服务底层的业务逻辑
"""


def clear_reports_logs(time):
    """
    删除指定时间之前 生成的报告和日志
      -mmin +1 -> 表示1分钟前的
      -mtime +1 -> 表示1天前的
    :param time:
    :return:
    """
    rm_log_cmd = "find '" + cfg.LOGS_PATH + "' -name '*.log' -mmin +" + str(time) + " -type f -exec rm -rf {} \\;"
    rm_report_cmd = "find '" + cfg.REPORTS_PATH + "history' -name '*.html' -mmin +" + str(time) + \
                    " -type f -exec rm -rf {} \\;"
    print(rm_log_cmd)
    print(rm_report_cmd)
    os.system(rm_log_cmd)
    os.system(rm_report_cmd)


def case_import_action(upload_file, import_method):
    """
    导入用例操作
    :param upload_file:
    :param import_method: 导入方式（批量新增、全部替换、批量替换）
    :return:
    """
    res_info = dict()
    if upload_file is None:
        res_info["msg"] = u"上传文件不能为空"
    elif ('.' not in upload_file.filename) or \
            (upload_file.filename.rsplit('.', 1)[1] not in ['xls', 'xlsx', 'csv']):
        res_info["msg"] = u"格式仅支持：.xls、.xlsx、.csv"
    else:
        log.info(import_method)
        log.info(upload_file)
        log.info(type(upload_file))
        res_info["msg"] = u"导入成功 ！"
    return res_info


# def case_import_mongo(pro_name):
#     """
#     更新项目测试用例数据 同步入mongo库中，默认状态为'下线'
#     :param pro_name:
#     :return:
#     【 备 注 】
#     1.run_status ：运行状态 （ pending 待运行、runninng 运行中、stopping 已停止）
#     2.start_time ：运行开始时间
#     3.run_time ：运行时间
#     """
#     test_class_list = get_test_class_list_by_pro_name(pro_name)
#     if test_class_list:
#         insert_list = []
#         now_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time()))
#         ISODate = parser.parse(now_str)
#         test_loader = unittest.TestLoader()
#         for test_class in test_class_list:
#             test_methods_name = test_loader.getTestCaseNames(test_class)
#             for test_method_name in test_methods_name:
#                 # 生成'测试方法'的实例对象，并反射获取'测试方法'
#                 test_instance = test_class(pro_name=pro_name, test_method=test_method_name)
#                 testMethod = getattr(test_instance, test_method_name)
#                 # 获取'测试方法'中的备注，作为'测试用例名称'
#                 test_case_name = testMethod.__doc__.split("\n")[0].strip()
#                 test_case_dict = {}
#                 test_case_dict["pro_name"] = pro_name
#                 test_case_dict["test_class_name"] = test_class.__name__
#                 test_case_dict["test_method_name"] = test_method_name
#                 test_case_dict["test_case_name"] = test_case_name
#                 test_case_dict["case_status"] = False
#                 test_case_dict["run_status"] = "stopping"
#                 test_case_dict["start_time"] = "----"
#                 test_case_dict["run_time"] = "----"
#                 test_case_dict["create_time"] = ISODate
#                 insert_list.append(test_case_dict)
#         # 将'测试用例'列表更新入对应项目的数据库中
#         with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
#             try:
#                 pro_db.drop()
#                 pro_db.insert_many(insert_list)
#             except Exception as e:
#                 mongo_exception_send_DD(e=e, msg="更新'" + pro_name + "'项目测试用例数据")
#                 return "mongo error"
#         return insert_list
#     else:
#         return "no such pro"
#
#
# def update_case_status(pro_name, test_method_name):
#     """
#     更新项目测试用例状态
#     :param pro_name:
#     :param test_method_name:
#     :return:
#     """
#     with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
#         try:
#             query_dict = {"test_method_name": test_method_name}
#             result = pro_db.find_one(query_dict, {"_id": 0})
#             old_case_status = result.get("case_status")
#             new_case_status = bool(1 - old_case_status)  # 布尔值取反
#             update_dict = {"$set": {"case_status": new_case_status}}
#             pro_db.update_one(query_dict, update_dict)
#             return new_case_status
#         except Exception as e:
#             mongo_exception_send_DD(e=e, msg="更新'" + pro_name + "'项目测试用例状态(单个)")
#             return "mongo error"
#
#
# def update_case_status_all(pro_name, case_status=False):
#     """
#     更新项目所有测试用例状态(上下线)
#     :param pro_name:
#     :param case_status:
#     :return: 返回 test_method_name_list 列表
#     """
#     with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
#         try:
#             update_dict = {"$set": {"case_status": case_status}}
#             pro_db.update({}, update_dict, multi=True)
#             results = pro_db.find({}, {"_id": 0})
#             return [res.get("test_method_name") for res in results]
#         except Exception as e:
#             mongo_exception_send_DD(e=e, msg="更新'" + pro_name + "'项目所有测试用例状态")
#             return "mongo error"


if __name__ == "__main__":
    pass
    # clear_screen_shot(4)
    # case_import_mongo("pro_demo_1")
    # update_case_status("pro_demo_1", "test_02")
    # update_case_status_all(pro_name="pro_demo_1", status=False)
    # get_progress_info("pro_demo_1")
    # print(get_case_run_status("pro_demo_1"))