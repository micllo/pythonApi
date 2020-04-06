# -*- coding:utf-8 -*-
from Config import config as cfg
import sys, os, time
from Tools.excel_data import read_excel
from Config.case_field_config import get_case_special_field_list, get_not_null_field_list, get_list_field,\
    get_not_null_field_list_with_depend
from Tools.mongodb import MongodbUtils
from Common.test_func import mongo_exception_send_DD
from Common.com_func import is_null, log
from dateutil import parser
from Tools.date_helper import get_current_iso_date
import unittest
import re
from bson.objectid import ObjectId
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
        line_dict["depend_field_value_list"] = []
        line_dict["actual_core_field_value_list"] = []
        line_dict["actual_field_name_list"] = []
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
    3.转换'is_depend'字段格式
    （1）是否为依赖接口：is_depend
        问题：<Excel> 显示 FALSE、TRUE  <python> 显示 0、1 （ int类型 )
        解决：将 int 或 '其他形式字符串' 转换成 bool 类型（ 其他形式字符串：空、"false"、"true"、"False"、"True"等)
    4.根据'is_depend'字段 检查必填项
    （1）若'is_depend=True：是依赖接口'
         1）验证依赖接口的必填项  get_not_null_field_list_with_depend()
         2）验证'depend_level'字段必须是 float 类型
    （2）若'is_depend=False：不是依赖接口'
         1）验证测试接口的必填项 get_not_null_field_list()
         2）验证'verify_mode'字段必须是 float 类型
        （ 备注：<Excel> 显示 1、2  <python> 显示 1.0、2.0 （ float类型 ) ）
    5.检查是否存在重复的用例
    （1）'接口名称'是否存在重复
    （2）'请求方式+接口地址'是否存在重复
    （3）'依赖等级'是否重复
    6.转换相关字段值的类型与格式
    （1）验证模式：verify_mode、depend_level
        问题：<Excel> 显示 1、2  <python> 显示 1.0、2.0 （ float类型 )
        解决：将 float 转换成 int 类型（ 若未填，则赋值 0  ）
    （2）用例状态：case_status
        问题：<Excel> 显示 FALSE、TRUE  <python> 显示 0、1 （ int类型 )
        解决：将 int 或 '其他形式字符串' 转换成 bool 类型（ 其他形式字符串：空、"false"、"true"、"False"、"True"等)
    （3）检查'请求头文件'和'请求参数'中是否存在中文逗号
    （4）将(以","分割)的相关字段值转换成list -> get_list_field()
        - 检查这些字段中是否存在中文逗号
        - < 里面的每一个元素的类型都是'str'（eg: "5"、"True") >
    （5）若存在'请求参数'，则需要检查是否以'?'或'{'开头
    7.检查'待比较关键字段名'列表与'期望的关键字段值'列表的数量是否一致
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

    # 3.转换'is_depend'字段格式
    for index, line_dict in enumerate(excel_list):
        for key, value in line_dict.items():
            if key.strip() == "is_depend":
                if type(value) is int:
                    line_dict[key] = value == 1 or False
                else:
                    line_dict[key] = value.strip() in ["true", "True", "TRUE"] or False

    # 4.根据'is_depend'字段 检查必填项
    for index, line_dict in enumerate(excel_list):
        if line_dict["is_depend"]:
            for key, value in line_dict.items():
                if key.strip() in get_not_null_field_list_with_depend() and str(value).strip() == "":
                    return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段不能为空", None
                if key.strip() == "depend_level" and not type(value) is float:
                        return "第 " + str(index + 2) + " 行的 < depend_level > 字段格式不正确", None
        else:
            for key, value in line_dict.items():
                if key.strip() in get_not_null_field_list() and str(value).strip() == "":
                    return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段不能为空", None
                if key.strip() == "verify_mode" and not type(value) is float:
                        return "第 " + str(index + 2) + " 行的 < verify_mode > 字段格式不正确", None

    # 5.检查是否存在重复的用例(接口名称、请求方式+接口地址)
    interface_name_list = []  # '接口名称'列表
    method_and_url_list = []  # '请求方式+接口地址'列表
    depend_level_list = []    # '依赖等级'列表
    for index, line_dict in enumerate(excel_list):
        interface_name_list.append(str(line_dict["interface_name"]).strip())
        method_and_url_list.append(str(line_dict["request_method"]).strip() + str(line_dict["interface_url"]).strip())
        if line_dict["is_depend"]:
            depend_level_list.append(str(int(line_dict["depend_level"])))

    interface_num_dict = {}  # 记录'接口名称'出现的次数 { "test_01": 1, "test_02": 2 }
    for interface_name in set(interface_name_list):
        interface_num_dict[interface_name] = interface_name_list.count(interface_name)
    for interface_name, num in interface_num_dict.items():
        if num > 1:
            return "interface_name = " + interface_name + " 字段重复出现了 " + str(num) + " 次", None

    method_and_url_num_dict = {}  # 记录'请求方式+接口地址'出现的次数 { "GET/test/add": 1, "POST/test/update": 2 }
    for method_and_url in set(method_and_url_list):
        method_and_url_num_dict[method_and_url] = method_and_url_list.count(method_and_url)
    for method_and_url, num in method_and_url_num_dict.items():
        if num > 1:
            return "request_method + interface_url = " + method_and_url + " 的组合重复出现了 " + str(num) + " 次", None

    if depend_level_list:
        depend_level_num_dict = {}  # 记录'依赖等级'出现的次数 { "1": 1, "2": 2 }
        for depend_level in set(depend_level_list):
            depend_level_num_dict[depend_level] = depend_level_list.count(depend_level)
        for depend_level, num in depend_level_num_dict.items():
            if num > 1:
                return "depend_level = " + depend_level + " 字段重复出现了 " + str(num) + " 次", None

    # 6.转换字段值的类型与格式
    for index, line_dict in enumerate(excel_list):
        for key, value in line_dict.items():
            if key.strip() in ["verify_mode", "depend_level"]:
                if type(value) is float:
                    line_dict[key] = int(value)
                else:
                    line_dict[key] = 0
            if key.strip() == "case_status":
                if type(value) is int:
                    line_dict[key] = value == 1 or False
                else:
                    line_dict[key] = value.strip() in ["true", "True", "TRUE"] or False
            if key.strip() in ["request_header", "request_params"]:
                if "，" in value.strip():
                    return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段存在中文逗号 ！", None
            if key.strip() in get_list_field():
                if value.strip() == "":
                    line_dict[key] = []
                else:
                    if "，" in value.strip():
                        return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段存在中文逗号 ！", None
                    else:
                        line_dict[key] = str(value.strip()).split(",")
            if key.strip() == "request_params":
                if value:
                    if not value.startswith("?") and not value.startswith("{"):
                        return "第 " + str(index + 2) + " 行的 " + key.strip() + " 字段值 必须以 ? 或 { 开头 ！", None

    # 7.检查'待比较关键字段名'列表与'期望的关键字段值'列表的数量是否一致'
    for index, line_dict in enumerate(excel_list):
        if len(line_dict["compare_core_field_name_list"]) != len(line_dict["expect_core_field_value_list"]):
            return "第 " + str(index + 2) + " 行的 'compare_core_field_name_list' 与 'expect_core_field_value_list' 字段数量不一致", None

    # show_excel_list(excel_list)
    return "验证通过", excel_list


def show_excel_list(excel_list):
    for index, line_dict in enumerate(excel_list):
        print("\n============== " + str(index) + " ================\n")
        for key, value in line_dict.items():
            print(key)
            print(value)
            print(type(value))
            print("--------")


def get_test_case(pro_name):
    """
    根据项目获取测试用例列表（上线的依赖接口排在前面）
    :param pro_name:
    :return: 返回值
    """
    test_case_list = []
    on_line_list_with_depend = []
    on_line_list_with_test = []
    off_line_list = []
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            results = pro_db.find({})
            for res in results:
                test_case_dict = dict()
                test_case_dict["_id"] = str(res.get("_id"))
                test_case_dict["interface_name"] = res.get("interface_name")
                test_case_dict["interface_url"] = res.get("interface_url")
                test_case_dict["request_method"] = res.get("request_method")
                test_case_dict["request_header"] = res.get("request_header")
                test_case_dict["request_params"] = res.get("request_params")
                test_case_dict["compare_core_field_name_list"] = res.get("compare_core_field_name_list")
                test_case_dict["expect_core_field_value_list"] = res.get("expect_core_field_value_list")
                test_case_dict["expect_field_name_list"] = res.get("expect_field_name_list")
                test_case_dict["verify_mode"] = res.get("verify_mode")
                test_case_dict["case_status"] = res.get("case_status")
                test_case_dict["is_depend"] = res.get("is_depend")
                test_case_dict["depend_level"] = res.get("depend_level")
                test_case_dict["depend_field_name_list"] = res.get("depend_field_name_list")
                test_case_dict["depend_field_value_list"] = res.get("depend_field_value_list")
                test_case_dict["actual_core_field_value_list"] = res.get("actual_core_field_value_list")
                test_case_dict["actual_field_name_list"] = res.get("actual_field_name_list")
                test_case_dict["update_time"] = res.get("update_time")
                test_case_dict["test_result"] = res.get("test_result")
                if res.get("case_status"):
                    if res.get("is_depend"):
                        on_line_list_with_depend.append(test_case_dict)
                    else:
                        on_line_list_with_test.append(test_case_dict)
                else:
                    off_line_list.append(test_case_dict)
            on_line_list_with_depend = sorted(on_line_list_with_depend, key=lambda keys: keys['depend_level'])
            test_case_list = on_line_list_with_depend + on_line_list_with_test + off_line_list
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目测试用例列表")
            return []
        finally:
            return test_case_list


def get_case_search_result(request_args, pro_name):
    """
    获取用例搜索结果
    :param request_args: GET请求参数
    :param pro_name:
    :return:
    【 搜 索 用 例 的 排 序 】
    1.上线的排在前面
    2.依赖接口排在前面
    3.依赖等级小的排在前面
    """
    search_pattern = {}
    if request_args:
        interface_name = request_args.get("interface_name", "").strip()
        interface_url = request_args.get("interface_url", "").strip()
        request_method = request_args.get("request_method", "").strip()
        case_status = request_args.get("case_status", "").strip()
        is_depend = request_args.get("is_depend", "").strip()
        if interface_name:
            search_pattern["interface_name"] = re.compile(interface_name)
        if interface_url:
            search_pattern["interface_url"] = re.compile(interface_url)
        if request_method:
            search_pattern["request_method"] = request_method
        if case_status:
            if case_status in ["true", "TRUE", "True"]:
                search_pattern["case_status"] = True
            else:
                search_pattern["case_status"] = False
        if is_depend:
            if is_depend in ["true", "TRUE", "True"]:
                search_pattern["is_depend"] = True
            else:
                search_pattern["is_depend"] = False

    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            if search_pattern:  # 判断是否存在搜索内容
                results = pro_db.find(search_pattern)
            else:
                results = pro_db.find({})
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目用例搜索结果")
            return []

    test_case_list = []
    on_line_list_with_depend = []
    on_line_list_with_test = []
    off_line_list = []
    if results:
        for res in results:
            test_case_dict = dict()
            test_case_dict["_id"] = str(res.get("_id"))
            test_case_dict["interface_name"] = res.get("interface_name")
            test_case_dict["interface_url"] = res.get("interface_url")
            test_case_dict["request_method"] = res.get("request_method")
            test_case_dict["request_header"] = str(res.get("request_header")).replace('"', "'")
            test_case_dict["request_params"] = str(res.get("request_params")).replace('"', "'")
            test_case_dict["compare_core_field_name_list"] = str(res.get("compare_core_field_name_list"))
            test_case_dict["expect_core_field_value_list"] = str(res.get("expect_core_field_value_list"))
            test_case_dict["expect_field_name_list"] = str(res.get("expect_field_name_list"))
            test_case_dict["verify_mode"] = res.get("verify_mode")
            test_case_dict["is_depend"] = res.get("is_depend")
            test_case_dict["depend_level"] = res.get("depend_level")
            test_case_dict["depend_field_name_list"] = str(res.get("depend_field_name_list"))
            test_case_dict["depend_field_value_list"] = str(res.get("depend_field_value_list"))
            test_case_dict["actual_core_field_value_list"] = str(res.get("actual_core_field_value_list"))
            test_case_dict["actual_field_name_list"] = str(res.get("actual_field_name_list"))
            test_case_dict["case_status"] = res.get("case_status")
            test_case_dict["update_time"] = str(res.get("update_time"))
            test_case_dict["test_result"] = res.get("test_result")
            if res.get("case_status"):
                if res.get("is_depend"):
                    on_line_list_with_depend.append(test_case_dict)
                else:
                    on_line_list_with_test.append(test_case_dict)
            else:
                off_line_list.append(test_case_dict)
        on_line_list_with_depend = sorted(on_line_list_with_depend, key=lambda keys: keys['depend_level'])
        test_case_list = on_line_list_with_depend + on_line_list_with_test + off_line_list
    return test_case_list


def get_case_operation_result(request_json, pro_name, mode):
    """
    获取用例添加结果
    :param request_json:
    :param pro_name:
    :param mode:  添加 add | 编辑 edit
    :return:
    【 添 加 步 骤 】
    1.验证'is_depend'字段不能为空
    2.转换'is_depend'字段格式 string -> bool
    3.根据'is_depend'字段 检查必填项
    4.检查需要转list的字段中是否存在中文的逗号
    5.若存在'请求参数'，则需要检查是否以'?'或'{'开头
    6.相关字段的格式转换
    （1）'用例状态' string -> bool
    （2）'列表字段' string -> list
    （3）'验证模式、依赖等级' string -> int （ 若为空，则赋值 0 ）
    7.检查'待比较关键字段名'列表与'期望的关键字段值'列表的数量是否一致
    8.整合公共的用例字段
    9.验证数据库中是否已存在
    （1）'接口名称'
    （2）'请求方式+接口地址'
    （3）'依赖等级' （若是依赖接口）
        （ 注意：若为'编辑'模式，则先排除编辑自身后，在进行上述判断 ）
    10.'新增'或'更新'用例数据

    【 字 段 格 式 】
    01.接口名称：interface_name（ 必填 ）
    02.接口地址：interface_url（ 必填 ）
    03.请求方式：request_method（ 必填 ）
    04.请求头文件：request_header
    05.请求参数：request_params
    06.验证模式：verify_mode（ 次必填 ）                            < (表单)string -> (Mongo)int >
    07.待比较关键字段名列表：compare_core_field_name_list（ 次必填 ） < (表单)string -> (Mongo)list >（以","分割）
    08.期望的关键字段值列表：expect_core_field_value_list（ 次必填 ） < (表单)string -> (Mongo)list >（以","分割）
    09.期望的响应字段列表：expect_field_name_list                   < (表单)string -> (Mongo)list >（以","分割）
    10.是否为依赖接口：is_depend  （ 必填 ）                         < (表单)string -> (Mongo)bool >
    11.依赖等级：depend_level    （ 次必填 ）                       < (表单)string  -> (Mongo)int >
    12.依赖字段名列表：depend_field_name_list                      < (表单)string -> (Mongo)list >（以","分割）
    13.用例状态：case_status                                      < (表单)string -> (Mongo)bool >
    """
    # 获取请求中的参数
    _id = request_json.get("_id", "").strip()
    interface_name = request_json.get("interface_name", "").strip()
    interface_url = request_json.get("interface_url", "").strip()
    request_method = request_json.get("request_method", "").strip()
    request_header = request_json.get("request_header", "").strip()
    request_params = request_json.get("request_params", "").strip()
    verify_mode = request_json.get("verify_mode", "").strip()
    compare_core_field_name_list = request_json.get("compare_core_field_name_list", "").strip()
    expect_core_field_value_list = request_json.get("expect_core_field_value_list", "").strip()
    expect_field_name_list = request_json.get("expect_field_name_list", "").strip()
    is_depend = request_json.get("is_depend", "").strip()
    depend_level = request_json.get("depend_level", "").strip()
    depend_field_name_list = request_json.get("depend_field_name_list", "").strip()
    case_status = request_json.get("case_status", "").strip()

    # 1.验证'is_depend'字段不能为空
    if is_depend == "":
        return "<是否为依赖接口> 未选择"

    log.info(is_depend)
    # 2.转换'is_depend'字段格式 string -> bool
    is_depend = is_depend in ["true", "TRUE", "True"]
    log.info(is_depend)

    # 3.根据'is_depend'字段 检查必填项
    if is_null(interface_name) or is_null(interface_url) or is_null(request_method):
        return "必填项 不能为空"
    if is_depend:
        if is_null(depend_level) or is_null(depend_field_name_list):
            return "依赖必填项 不能为空"
    else:
        if is_null(verify_mode) or is_null(compare_core_field_name_list) or is_null(expect_core_field_value_list):
            return "测试必填项 不能为空"

    # 4.检查需要转list的字段中是否存在中文的逗号
    for each in [request_header, request_params, compare_core_field_name_list, expect_core_field_value_list,
                 expect_field_name_list, depend_field_name_list]:
        if "，" in each:
            return "相关列表字段中 存在中文逗号 ！"

    # 5.若存在'请求参数'，则需要检查是否以'?'或'{'开头
    if request_params:
        if not request_params.startswith("?") and not request_params.startswith("{"):
            return "'请求参数' 必须以 ? 或 { 开头 ！"

    # 6.相关字段的格式转换
    case_status = case_status in ["true", "TRUE", "True"]
    verify_mode = verify_mode != "" and int(verify_mode) or 0
    depend_level = depend_level != "" and int(depend_level) or 0
    # 若为空则赋值[],否则赋值['aa','bb']
    compare_core_field_name_list = compare_core_field_name_list != "" and str(compare_core_field_name_list.strip()).split(",") or []
    expect_core_field_value_list = expect_core_field_value_list != "" and str(expect_core_field_value_list.strip()).split(",") or []
    expect_field_name_list = expect_field_name_list != "" and str(expect_field_name_list.strip()).split(",") or []
    depend_field_name_list = depend_field_name_list != "" and str(depend_field_name_list.strip()).split(",") or []

    # 7.检查'待比较关键字段名'列表与'期望的关键字段值'列表的数量是否一致
    if len(compare_core_field_name_list) != len(expect_core_field_value_list):
        return "<待比较的关键字段名> 与 <期望的关键字段值> 数量必须一致"

    # 8.整合公共的用例字段
    current_iso_date = get_current_iso_date()
    test_case_dict = {"interface_name": interface_name, "interface_url": interface_url, "request_method": request_method,
                      "request_header": request_header, "request_params": request_params, "verify_mode": verify_mode,
                      "compare_core_field_name_list": compare_core_field_name_list, "expect_core_field_value_list": expect_core_field_value_list,
                      "expect_field_name_list": expect_field_name_list, "is_depend": is_depend, "depend_level": depend_level,
                      "depend_field_name_list": depend_field_name_list, "case_status": case_status, "update_time": current_iso_date}

    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            if mode == "edit":
                # 9.验证数据库中是否已存在
                old_case_dict = pro_db.find_one({"_id": ObjectId(_id)})
                old_interface_name = old_case_dict.get("interface_name")
                old_request_method = old_case_dict.get("request_method")
                old_interface_url = old_case_dict.get("interface_url")
                old_depend_level = old_case_dict.get("depend_level")
                if interface_name != old_interface_name:
                    interface_name_case = pro_db.find_one({"interface_name": interface_name})
                    if interface_name_case: return "接口名称 已存在 ！"
                if request_method != old_request_method or interface_url != old_interface_url:
                    method_and_url_case = pro_db.find_one({"request_method": request_method, "interface_url": interface_url})
                    if method_and_url_case: return "请求方式 + 接口地址 已存在 ！"
                if is_depend and depend_level != old_depend_level:
                    depend_level_case = pro_db.find_one({"depend_level": depend_level})
                    if depend_level_case: return "依赖等级 已存在 ！"
                # 更新用例
                pro_db.update({"_id": ObjectId(_id)}, {"$set": test_case_dict})
            else:  # add
                interface_name_case = pro_db.find_one({"interface_name": interface_name})
                if interface_name_case: return "接口名称 已存在 ！"
                method_and_url_case = pro_db.find_one({"request_method": request_method, "interface_url": interface_url})
                if method_and_url_case: return "请求方式 + 接口地址 已存在 ！"
                if is_depend:
                    depend_level_case = pro_db.find_one({"depend_level": depend_level})
                    if depend_level_case: return "依赖等级 已存在 ！"
                # 新增用例
                test_case_dict["response_info"] = ""
                test_case_dict["depend_field_value_list"] = []
                test_case_dict["actual_core_field_value_list"] = []
                test_case_dict["actual_field_name_list"] = []
                test_case_dict["result_core_field_value"] = ""
                test_case_dict["result_field_name_list"] = ""
                test_case_dict["test_result"] = ""
                test_case_dict["create_time"] = current_iso_date
                pro_db.insert(test_case_dict)
        except Exception as e:
            log.error(e)
            mongo_exception_send_DD(e=e, msg="为'" + pro_name + "'项目'" + mode + "'测试用例")
            return "mongo error"
    return mode == "add" and "新增成功 ！" or "更新成功 ！"


def get_case_del_result(request_json, pro_name):
    """
    获取用例删除结果
    :param request_json:
    :param pro_name:
    :return:
    """
    # 获取请求中的参数
    _id = request_json.get("_id", "").strip()
    query_dict = {"_id": ObjectId(_id)}
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            remove_case = pro_db.find_one(query_dict)
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="为'" + pro_name + "'项目删除测试用例")
            return "mongo error"

    if remove_case:
        pro_db.remove(query_dict)
        return "该用例删除成功 ！"
    else:
        return "要删除的用例不存在 ！ "


def get_case_by_id(request_args, pro_name):
    """
    通过id获取用例（填充编辑弹层）
    :param request_args:
    :param pro_name:
    :return:
      【 字 段 格 式 】
      01.接口名称：interface_name（ 必填 ）
      02.接口地址：interface_url（ 必填 ）
      03.请求方式：request_method（ 必填 ）
      04.请求头文件：request_header
      05.请求参数：request_params
      06.验证模式：verify_mode（ 测试必填 ）                            < (Mongo)int -> (表单)string >
      07.待比较关键字段名列表：compare_core_field_name_list（ 测试必填 ）< (Mongo)list -> (表单)string >（以","分割）
      08.期望的关键字段值列表：expect_core_field_value_list（ 测试必填 ）< (Mongo)list -> (表单)string >（以","分割）
      09.期望的响应字段列表：expect_field_name_list                    < (Mongo)list -> (表单)string >（以","分割）
      10.是否为依赖接口：is_depend              （ 必填 ）             < (Mongo)bool -> (表单)string >
      11.依赖等级：depend_level                （ 依赖必填 ）          < (Mongo)int -> (表单)string >
      12.依赖字段名列表：depend_field_name_list                       < (Mongo)list -> (表单)string >（以","分割）
      13.用例状态：case_status                                       < (Mongo)bool -> (表单)string >

      < 以下字段不显示在导入表单中>
      14.响应信息：response_info
      15.依赖字段值列表：depend_field_value_list              < (Mongo)list -> (表单)string >（以","分割）
      16.实际的关键字段值列表：actual_core_field_value_list    < (Mongo)list -> (表单)string >（以","分割）
      17.实际的响应字段列表：actual_field_name_list
      18.关键字段值比较结果：result_core_field_value
      19.响应字段列表比较结果：result_field_name_list
      20.测试结果：test_result
      21.创建时间：create_time   < (Mongo)ISODate -> (表单)string >
      22.更新时间：update_time   < (Mongo)ISODate -> (表单)string >

    """
    _id = request_args.get("_id", "").strip()
    query_dict = {"_id": ObjectId(_id)}
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            test_case_dict = pro_db.find_one(query_dict)
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="通过id获取'" + pro_name + "'项目的测试用例")
            return "mongo error"

    # 将所有字段转换成 string 类型
    for field, value in test_case_dict.items():
        # 若"验证模式、依赖等级"为0，则赋空值 传递给编辑弹层显示
        if field in ["verify_mode", "depend_level"]:
            test_case_dict[field] = value != 0 and str(value) or ""

        if field in ["_id", "case_status", "is_depend", "create_time", "update_time"]:
            test_case_dict[field] = str(value)

        if field in get_list_field():
            test_case_dict[field] = ",".join(value)

    return test_case_dict


if __name__ == "__main__":
    pass
    # verify_result, excel_list = verify_excel_and_transfer_format(cfg.UPLOAD_CASE_FILE)
    # if verify_result == "验证通过":
    #     import_mongodb("pro_demo_1", excel_list, "all_replace")  # batch_insert、all_replace、batch_insert_and_replace
    # else:
    #     print(verify_result)




# # param = "{'image_id':'{{image_id}}', 'token':'{{token}}'}"
#     # param = "?token={{token}}"
#     # param = "?token={{token}}&test={{test}}"
#     param = "/test/add/{{token}}"
#
#     depend_dict = {"token": "2222222", "image_id": "11111"}
#
#     # 获取参数中的依赖字段列表
#     params_depend_field_list = []
#     num = param.count('{{')  # 统计参数的依赖字段数量
#     pattern = r'.*{{(.*)}}' * num  # 整理匹配模式（捕获数量）
#     if pattern:  # 若存在 则进行捕获
#         match_obj = re.match(pattern, param)
#         for i in range(num):
#             params_depend_field_list.append(match_obj.group(i + 1))
#     print(params_depend_field_list)
#
#     # 判断参数中的依赖字段值是否都已获取
#     #（ 判断'params_depend_field_list'列表中的每个字段是否都包含在'depend_dict'的'key'列表中）
#     no_contain_depend_field_list = [field for field in params_depend_field_list if field not in list(depend_dict.keys())]
#     print(no_contain_depend_field_list)
#     if no_contain_depend_field_list:
#         print("依赖字段没有全部获取到")
#     else:
#         # 替换依赖字段
#         for field in params_depend_field_list:
#             param = param.replace("{{" + field + "}}", depend_dict[field])
#
#     print(param)