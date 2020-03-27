# -*- coding:utf-8 -*-
from Config import config as cfg
import sys, os, time
from Tools.excel_data import read_excel
from Config.case_field_config import get_case_special_field_list, get_not_null_field_list, get_list_field
from Tools.mongodb import MongodbUtils
from Common.test_func import mongo_exception_send_DD
from Common.com_func import is_null
from dateutil import parser
from Tools.date_helper import get_current_iso_date
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


def case_import_action(pro_name, upload_file, import_method):
    """
    导入用例操作
    :param pro_name
    :param upload_file:
    :param import_method: 导入方式（批量新增、全部替换、批量新增+替换）
    :return:
    """
    res_info = dict()
    if upload_file is None:
        res_info["msg"] = u"上传文件不能为空"
    elif ('.' not in upload_file.filename) or \
            (upload_file.filename.rsplit('.', 1)[1] not in ['xls', 'xlsx', 'csv']):
        res_info["msg"] = u"格式仅支持：.xls、.xlsx、.csv"
    else:
        # 将上传的文件保存入指定Excel文件中
        upload_file.save(cfg.UPLOAD_CASE_FILE)
        # 验证Excel用例格式
        verify_result, excel_list = verify_excel_and_transfer_format(cfg.UPLOAD_CASE_FILE)
        res_info["msg"] = verify_result
        if verify_result == "验证通过":
            res_info["msg"] = import_mongodb(pro_name, excel_list, import_method)
    return res_info


def import_mongodb(pro_name, excel_list, import_method):
    """
    将excel中的用例按照导入方式，导入mongo
    :param pro_name
    :param excel_list:
    :param import_method: 导入方式（batch_insert、all_replace、batch_insert_and_replace）
    :return:
    【 备 注 】
    all_replace：先清空数据库，然后全部插入
    batch_insert：区分'不在数据库中的用例列表'和'需要更新的用例列表'，只执行插入操作
    batch_insert_and_replace：区分'不在数据库中的用例列表'和'需要更新的用例列表'，分别执行插入和更新操作
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:

            if import_method == "all_replace":
                pro_db.drop()
                pro_db.insert_many(filled_other_field(excel_list))
                return "全部替换 操作成功 ！"
            else:
                # 获取数据库中的'接口名称列表'
                all_case_in_db = pro_db.find()
                interface_name_list_in_db = [case.get("interface_name") for case in all_case_in_db]
                # 区分'不在数据库中的用例列表'和'需要更新的用例列表'
                update_list = []
                insert_list = []
                for index, line_dict in enumerate(excel_list):
                    if line_dict["interface_name"] in interface_name_list_in_db:
                        update_list.append(line_dict)
                    else:
                        insert_list.append(line_dict)

                if import_method == "batch_insert":
                    # 插入新增的数据
                    if not is_null(insert_list):
                        pro_db.insert_many(filled_other_field(insert_list))
                    return "批量新增 操作成功 ！"
                else:  # batch_insert_and_replace
                    if not is_null(insert_list):
                        pro_db.insert_many(filled_other_field(insert_list))
                    # 更新数据
                    if not is_null(update_list):
                        for line_dict in update_list:
                            line_dict["update_time"] = get_current_iso_date()
                            query_dict = {"interface_name": line_dict["interface_name"]}
                            update_dict = {"$set": line_dict}
                            pro_db.update(query_dict, update_dict)
                    return "批量新增+替换 操作成功 ！"
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="导入'" + pro_name + "'项目excel测试用例数据")
            return "mongo error"


def filled_other_field(excel_list):
    """
    【 填补其他的字段 】
    :param excel_list:
    :return:
    """
    current_iso_date = get_current_iso_date()
    for index, line_dict in enumerate(excel_list):
        line_dict["response_info"] = ""
        line_dict["actual_core_field_value"] = []
        line_dict["result_core_field_value"] = ""
        line_dict["result_field_name_list"] = ""
        line_dict["test_result"] = ""
        line_dict["create_time"] = current_iso_date
        line_dict["update_time"] = current_iso_date
    # show_excel_list(excel_list)
    return excel_list


def verify_excel_and_transfer_format(excel_file):
    """
    【 验 证 并 装 换 Excel 用 例 格 式 】
    1.获取用例字段名列表（去除前后空格）
    2.判断用例字段名是否正确 -> get_case_special_field_list()
    （1）是否有多余的字段
    （2）是否有缺失的字段
    3.检查必填项 -> get_not_null_field_list()
    4.检查是否存在重复的用例(接口名称)
    5.转换相关字段值的类型与格式
    （1）验证模式：verify_mode
        问题：<Excel> 显示 1、2  <python> 显示 1.0、2.0 （ float类型 )
        解决：将 float 转换成 int 类型
    （2）用例状态：case_status
        问题：<Excel> 显示 FALSE、TRUE  <python> 显示 0、1 （ int类型 )
        解决：将 int 或 '其他形式字符串' 转换成 bool 类型（ 其他形式字符串：空、"false"、"true"、"False"、"True"等)
    （3）将(以","分割)的相关字段值转换成list -> get_list_field()
        - 检查这些字段中是否存在中文逗号
        - < 里面的每一个元素的类型都是'str'（eg: "5"、"True") >
    """
    # 读取Excel用例文件
    excel_list = read_excel(excel_file, 0)

    if excel_list == []:
        return "上传的excel文件中没有用例", None

    # 1.获取用例字段名列表（去除前后空格）
    case_field_list = list(excel_list[0].keys())

    # 2.判断用例字段名是否正确
    case_special_field_list = get_case_special_field_list()
    for special_each in case_special_field_list:
        if special_each not in case_field_list:
            return "缺失相关的列", None
    for each in case_field_list:
        if each not in case_special_field_list:
            return "存在多余的列", None

    # 3.检查必填项
    interface_name_list = []
    for index, line_dict in enumerate(excel_list):
        for key, value in line_dict.items():
            if key.strip() in get_not_null_field_list() and str(value).strip() == "":
                return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段不能为空", None
            if key.strip() == "interface_name":
                interface_name_list.append(value)

    # 4.检查是否存在重复的用例(接口名称)
    interface_num_dict = {}
    for interface_name in set(interface_name_list):
        interface_num_dict[interface_name] = interface_name_list.count(interface_name)
    for interface_name, num in interface_num_dict.items():
        if num > 1:
            return "interface_name = " + interface_name + " 字段重复出现了 " + str(num) + " 次", None

    # 5.转换字段值的类型与格式
    for index, line_dict in enumerate(excel_list):
        for key, value in line_dict.items():
            if key.strip() == "verify_mode":
                line_dict[key] = int(value)
            if key.strip() == "case_status":
                if type(value) is int:
                    line_dict[key] = value == 1 or False
                else:
                    line_dict[key] = value.strip() in ["true", "True", "TRUE"] or False
            if key.strip() in get_list_field():
                if value.strip() == "":
                    line_dict[key] = []
                else:
                    if "，" in value.strip():
                        return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段存在中文逗号 ！", None
                    else:
                        line_dict[key] = str(value.strip()).split(",")

    # show_excel_list(excel_list)
    return "验证通过", excel_list


def show_excel_list(excel_list):
    for index, line_dict in enumerate(excel_list):
        print("\n======= " + str(index) + " =========\n")
        for key, value in line_dict.items():
            print(value)
            print(type(value))


def get_test_case(pro_name):
    """
    根据项目获取测试用例列表（上线的排在前面）
    :param pro_name:
    :return: 返回值
    """
    test_case_list = []
    on_line_list = []
    off_line_list = []
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            results = pro_db.find({}, {"_id": 0})
            for res in results:
                test_case_dict = dict()
                test_case_dict["interface_name"] = res.get("interface_name")
                test_case_dict["interface_url"] = res.get("interface_url")
                test_case_dict["request_method"] = res.get("request_method")
                test_case_dict["request_params"] = res.get("request_params")
                test_case_dict["verify_mode"] = res.get("verify_mode")
                test_case_dict["case_status"] = res.get("case_status")
                test_case_dict["update_time"] = res.get("update_time")
                if res.get("case_status"):
                    on_line_list.append(test_case_dict)
                else:
                    off_line_list.append(test_case_dict)
            test_case_list = on_line_list + off_line_list
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目测试用例列表")
            return "mongo error"
        finally:
            return test_case_list


if __name__ == "__main__":
    pass
    verify_result, excel_list = verify_excel_and_transfer_format(cfg.UPLOAD_CASE_FILE)
    if verify_result == "验证通过":
        import_mongodb("pro_demo_1", excel_list, "batch_insert_and_replace")  # batch_insert、all_replace、batch_insert_and_replace
    else:
        print(verify_result)