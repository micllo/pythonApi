# -*- coding:utf-8 -*-
from Env import env_config as cfg
import os, time
from Tools.excel_data import read_excel, set_style
from Config.case_field_config import get_case_special_field_list, get_not_null_field_list, get_list_field,\
    get_not_null_field_list_with_depend
from Tools.mongodb import MongodbUtils
from Common.com_func import is_null, log, mongo_exception_send_DD, ping_host, send_DD, api_monitor_send_DD, mkdir
from Tools.date_helper import get_current_iso_date
import re
from bson.objectid import ObjectId
from Config.pro_config import get_pro_host
from Config.case_field_config import get_case_field_name
from Common.verify_interface import VerifyInterface
from Common.acquire_depend import AcquireDependField
from Tools.decorator_tools import async
import xlwt
# sys.path.append("./")


"""
api 服务底层的业务逻辑
"""


def clear_reports_logs(time, pro_name):
    """
    删除指定时间之前 生成的报告和日志
      -mmin +1 -> 表示1分钟前的
      -mtime +1 -> 表示1天前的
    :param time:
    :param pro_name:
    :return:
    """
    rm_log_cmd = "find '" + cfg.LOGS_DIR + "' -name '*.log' -mmin +" + str(time) + " -type f -exec rm -rf {} \\;"
    rm_report_cmd = "find '" + cfg.REPORTS_DIR + pro_name + "/history' -name '*.xls' -mmin +" + str(time) + \
                    " -type f -exec rm -rf {} \\;"
    print(rm_log_cmd)
    print(rm_report_cmd)
    os.system(rm_log_cmd)
    os.system(rm_report_cmd)


def pro_is_running(pro_name):
    """
    判断项目是否在运行
    :param pro_name:
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        run_status_case_list = []
        try:
            run_status_case_cursor = pro_db.find({"run_status": True})
            run_status_case_list = [each for each in run_status_case_cursor]
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目运行状态列表")
        finally:
            is_run = len(run_status_case_list) != 0
            return is_run


def set_pro_run_status(pro_name, run_status=False):
    """
    设置项目'所有'的'测试用例'的运行状态
    :param pro_name:
    :param run_status:
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            pro_db.update({}, {"$set": {"run_status": run_status}}, multi=True)
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="设置'" + pro_name + "'项目所有用例的运行状态")
            return "mongo error"


def run_test_by_pro(host_name, pro_name, run_type):
    """
    运行测试
    :param host_name
    :param pro_name:
    :param run_type: 运行方式：定时 cron、手动 manual
    :return:
        1.<判断>相关信息
           host是否可以ping通
        2.获取上线的接口列表
         （1）上线的'依赖接口列表'
         （2）上线的'测试接口列表'
          <判断>是否存在 上线的'测试接口列表'
        3.若 存在错误信息
        （1）直接返回
        （2）若是 定时任务，则需要钉钉通知
        4.异步执行 接口测试
    """
    error_msg = ""
    host = get_pro_host(pro_name, host_name)
    if is_null(pro_name):
        error_msg = "项目名不能为空"
    elif is_null(host_name):
        error_msg = "HOST不能为空"
    elif is_null(get_pro_host(pro_name, host_name)):
        error_msg = "HOST错误"
    elif pro_is_running(pro_name):
        error_msg = "当前项目正在运行中"
    elif not ping_host(host=host, check_num=5):
        error_msg = "本地无法 ping 通 HOST"

    if error_msg:
        if run_type == "cron":
            text = "#### '" + pro_name + "'项目 定时任务执行 提示：" + error_msg
            send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title=pro_name, text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)
        return error_msg

    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            depend_interface_list = pro_db.find({"case_status": True, "is_depend": True})
            test_interface_list = pro_db.find({"case_status": True, "is_depend": False})
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目上线接口列表")
            return "mongo error"

    depend_interface_list = list(depend_interface_list)
    test_interface_list = list(test_interface_list)

    if is_null(test_interface_list):
        return"没有上线的用例"

    test_interface(pro_name=pro_name, host=host, depend_interface_list=depend_interface_list,
                   test_interface_list=test_interface_list)
    return "测试进行中"


@async
def test_interface(pro_name, host, depend_interface_list, test_interface_list):
    """
    【 测 试 接 口 】（根据项目名）
    :param pro_name:
    :param host:
    :param depend_interface_list:
    :param test_interface_list:
    :return:

        【 测 试 流 程 】
        1.将项目'运行状态'设置为开启
        2.获取依赖字段值
           < 判断 > 是否需要执行依赖：
         （1）若不需要 则 直接进入'验证接口'步骤
         （2）若需要 则获取依赖字段：
              1）若获取成功，则替换接口中的相应变量、进入'验证接口'步骤
              2）若获取失败，则不进行接口验证
              （ 备注：通过 'verify_flag' 标记进行控制 ）
        3.验证接口
        （1）执行测试，获取测试结果列表
        （2）更新测试结果
        4.将项目'运行状态'设置为停止
        5.若存在'失败'或'错误'则发送钉钉
    """
    # 1.将项目'运行状态'设置为开启
    set_pro_run_status(pro_name=pro_name, run_status=True)

    # 2.获取依赖字段值
    adf = AcquireDependField(pro_name=pro_name, host=host, depend_interface_list=depend_interface_list,
                             test_interface_list=test_interface_list)
    if adf.is_need_depend():
        test_interface_list = adf.acquire()

    # 3.验证接口
    error_list = []
    fail_list = []
    if adf.verify_flag:

        # 执行测试，获取测试结果列表
        id_result_dict = {}   # {"_id":{"test_resuld":"success", "":""}, "_id":{}, }

        # host = "http://www.google.com.hk"  # 测试重试次数使用

        for test_interface in test_interface_list:
            result_dict = VerifyInterface(interface_name=test_interface.get("interface_name"),
                                          host=host, interface_url=test_interface.get("interface_url"),
                                          request_method=test_interface.get("request_method"),
                                          request_header=test_interface.get("request_header"),
                                          request_params=test_interface.get("request_params"),
                                          verify_mode=test_interface.get("verify_mode"),
                                          compare_core_field_name_list=test_interface.get("compare_core_field_name_list"),
                                          expect_core_field_value_list=test_interface.get("expect_core_field_value_list"),
                                          expect_field_name_list=test_interface.get("expect_field_name_list"),
                                          depend_interface_list=test_interface.get("depend_interface_list"),
                                          depend_field_name_list=test_interface.get("depend_field_name_list")).verify()
            id_result_dict[test_interface.get("_id")] = result_dict

        # 更新测试结果
        with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
            update_time = get_current_iso_date()
            for _id, test_info in id_result_dict.items():
                test_info["update_time"] = update_time
                pro_db.update({"_id": _id}, {"$set": test_info})
                if "error" in test_info["test_result"]: error_list.append(test_info["test_result"])
                if "fail" in test_info["test_result"]: fail_list.append(test_info["test_result"])

    # 4.将项目'运行状态'设置为停止
    set_pro_run_status(pro_name=pro_name, run_status=False)

    # 5.若存在'失败'或'错误'则发送钉钉
    if fail_list:
        api_monitor_send_DD(pro_name=pro_name, wrong_type="fail")
    elif error_list:
        api_monitor_send_DD(pro_name=pro_name, wrong_type="error")


def update_case_status_all(pro_name, case_status=False):
    """
    更新项目所有测试用例状态(上下线)
    :param pro_name:
    :param case_status:
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            update_dict = {"$set": {"case_status": case_status}}
            pro_db.update({}, update_dict, multi=True)
            return "done"
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="更新'" + pro_name + "'项目所有测试用例状态")
            return "mongo error"


def update_case_status(pro_name, _id):
    """
    更新项目测试用例状态
    :param pro_name:
    :param _id:
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            query_dict = {"_id": ObjectId(_id)}
            result = pro_db.find_one(query_dict, {"_id": 0})
            old_case_status = result.get("case_status")
            new_case_status = bool(1 - old_case_status)  # 布尔值取反
            update_dict = {"$set": {"case_status": new_case_status}}
            pro_db.update_one(query_dict, update_dict)
            return new_case_status
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="更新'" + pro_name + "'项目测试用例状态(单个)")
            return "mongo error"


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
    elif pro_is_running(pro_name):
        res_info["msg"] = u"当前项目正在运行中"
    else:
        # 将上传的文件保存入指定Excel文件中
        mkdir(cfg.UPLOAD_CASE_DIR)
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
        line_dict["run_status"] = False
        line_dict["update_time"] = current_iso_date
        line_dict["create_time"] = current_iso_date
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
    4.检查'request_method'字段是否正确
    5.根据'is_depend'字段 检查必填项
    （1）若'is_depend=True：是依赖接口'
         1）验证依赖接口的必填项  get_not_null_field_list_with_depend()
         2）验证'depend_level'字段必须是 float 类型
    （2）若'is_depend=False：不是依赖接口'
         1）验证测试接口的必填项 get_not_null_field_list()
         2）验证'verify_mode'字段必须是 float 类型
        （ 备注：<Excel> 显示 1、2  <python> 显示 1.0、2.0 （ float类型 ) ）
    6.检查是否存在重复的用例
    （1）'接口名称'是否存在重复
    （2）'请求方式+接口地址'是否存在重复
    （3）'依赖等级'是否重复
    7.转换相关字段值的类型与格式
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
    8.检查'待比较关键字段名'列表与'期望的关键字段值'列表的数量是否一致
    """
    # 读取Excel用例文件（第一个工作表）
    excel_list = read_excel(filename=excel_file, sheet_index=0, set_head_row_num=1)
    for line in excel_list:
        print(line)
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

    # 4.检查'request_method'字段是否正确
    for index, line_dict in enumerate(excel_list):
        for key, value in line_dict.items():
            if key.strip() == "request_method":
                if value.upper() in ["GET", "POST", "PUT", "DELETE"]:
                    line_dict[key] = value.upper()
                else:
                    return "第 " + str(index + 3) + " 行的 < 请求方式 > 字段格式不正确", None

    # 5.根据'is_depend'字段 检查必填项
    for index, line_dict in enumerate(excel_list):
        if line_dict["is_depend"]:
            for key, value in line_dict.items():
                if key.strip() in get_not_null_field_list_with_depend() and str(value).strip() == "":
                    return "第 " + str(index + 3) + " 行的 " + key.strip() + " 字段不能为空", None
                if key.strip() == "depend_level" and not type(value) is float:
                        return "第 " + str(index + 3) + " 行的 < 依赖等级 > 字段格式不正确", None
        else:
            for key, value in line_dict.items():
                if key.strip() in get_not_null_field_list() and str(value).strip() == "":
                    return "第 " + str(index + 3) + " 行的 " + key.strip() + " 字段不能为空", None
                if key.strip() == "verify_mode" and not type(value) is float:
                        return "第 " + str(index + 3) + " 行的 < 验证模式 > 字段格式不正确", None

    # 6.检查是否存在重复的用例(接口名称、请求方式+接口地址)
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

    # 7.转换字段值的类型与格式
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
                    return "第 " + str(index + 3) + " 行的 " + key.strip() + " 字段存在中文逗号 ！", None
            if key.strip() in get_list_field():
                if value.strip() == "":
                    line_dict[key] = []
                else:
                    if "，" in value.strip():
                        return "第 " + str(index + 3) + " 行的 " + key.strip() + " 字段存在中文逗号 ！", None
                    else:
                        line_dict[key] = str(value.strip()).split(",")
            if key.strip() == "request_params":
                if value:
                    if not value.startswith("?") and not value.startswith("{"):
                        return "第 " + str(index + 3) + " 行的 " + key.strip() + " 字段值 必须以 ? 或 { 开头 ！", None

    # 8.检查'待比较关键字段名'列表与'期望的关键字段值'列表的数量是否一致'
    for index, line_dict in enumerate(excel_list):
        if len(line_dict["compare_core_field_name_list"]) != len(line_dict["expect_core_field_value_list"]):
            return "第 " + str(index + 3) + " 行的<待比较关键字段名列表>与<期望的关键字段值列表>字段数量不一致", None

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
    :return: 用例列表、用例数量、是否存在运行的用例
    """
    test_case_list = []
    on_line_list_with_depend = []
    on_line_list_with_test = []
    off_line_list = []
    case_num = 0
    run_case_list = []
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            results_cursor = pro_db.find({})
            for res in results_cursor:
                case_num += 1
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
                if res.get("run_status"):
                    run_case_list.append(res.get("run_status"))
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
            return [], 0, False
        finally:
            is_run = len(run_case_list) != 0
            return test_case_list, case_num, is_run


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
        test_result = request_args.get("test_result", "").strip()
        is_depend = request_args.get("is_depend", "").strip()
        if interface_name:
            search_pattern["interface_name"] = re.compile(interface_name)
        if interface_url:
            search_pattern["interface_url"] = re.compile(interface_url)
        if test_result:
            search_pattern["test_result"] = re.compile(test_result)
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
    case_num = 0
    if results:
        for res in results:
            case_num += 1
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
    return test_case_list, case_num, pro_is_running(pro_name)


def get_case_operation_result(request_json, pro_name, mode):
    """
    获取用例添加结果
    :param request_json:
    :param pro_name:
    :param mode:  添加 add | 编辑 edit
    :return:
    【 添 加 步 骤 】
    0.若项目在运行中，不能进行编辑
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

    # 0.若项目在运行中，不能进行编辑
    if pro_is_running(pro_name) and mode == "edit":
        return "当前项目正在运行中"

    # 1.验证'is_depend'字段不能为空
    if is_depend == "":
        return "<是否为依赖接口> 未选择"

    # 2.转换'is_depend'字段格式 string -> bool
    is_depend = is_depend in ["true", "TRUE", "True"]

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
                      "expect_field_name_list": expect_field_name_list, "is_depend": is_depend, "depend_field_name_list": depend_field_name_list,
                      "depend_level": depend_level, "case_status": case_status}

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
                test_case_dict["run_status"] = False
                test_case_dict["update_time"] = current_iso_date
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
    # 判断是否在运行中
    if pro_is_running(pro_name):
        return "当前项目正在运行中"

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
      17.实际的响应字段列表：actual_field_name_list            < (Mongo)list -> (表单)string >（以","分割）
      18.关键字段值比较结果：result_core_field_value
      19.响应字段列表比较结果：result_field_name_list
      20.测试结果：test_result
      21.运行状态：run_status    < (Mongo)bool -> (表单)string >
      22.创建时间：create_time   < (Mongo)ISODate -> (表单)string >
      23.更新时间：update_time   < (Mongo)ISODate -> (表单)string >

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

        if field in ["_id", "case_status", "is_depend", "create_time", "update_time", "run_status"]:
            test_case_dict[field] = str(value)

        if field in get_list_field():
            test_case_dict[field] = ",".join(value)

    return test_case_dict


def statis_case(pro_name):
    """
    统计用例：成功、失败、错误、下线、依赖
    :param pro_name:
    :return:
    【 步 骤 】
        1.获取所有用例
        2.将所有字段格式转换成string
        3.统计区分
        {"success_1":[], "fail_2":[], "error_1":[], "depend_2":[], "offline_3":[]}
    """
    # 获取所有用例
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            all_cursor = pro_db.find({}, {"_id": 0})
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="统计'" + pro_name + "'项目用例")
            return "mongo error"

    # 将所有字段格式转换成string
    all_case_list = [each for each in all_cursor]
    for case_dict in all_case_list:
        for field, value in case_dict.items():
            # 若"验证模式、依赖等级"为0，则赋空值
            if field in ["verify_mode", "depend_level"]:
                # case_dict[field] = value != 0 and str(value) or ""
                if value == 0:
                    case_dict[field] = ""
            if field in ["_id", "case_status", "is_depend", "run_status", "create_time", "update_time"]:
                case_dict[field] = str(value)
            if field in get_list_field():
                case_dict[field] = ",".join(value)

    # 统计区分
    statis_dict = {}
    success_case_list = []
    fail_case_list = []
    error_case_list = []
    depend_case_list = []
    offline_case_list = []
    for case_dict in all_case_list:
        if case_dict["is_depend"] == "True":
            depend_case_list.append(case_dict)
        else:
            if case_dict["case_status"] == "False":
                offline_case_list.append(case_dict)
            else:
                if "success" in case_dict["test_result"]:
                    success_case_list.append(case_dict)
                elif "fail" in case_dict["test_result"]:
                    fail_case_list.append(case_dict)
                else:
                    error_case_list.append(case_dict)
    statis_dict["success_" + str(len(success_case_list))] = success_case_list
    statis_dict["fail_" + str(len(fail_case_list))] = fail_case_list
    statis_dict["error_" + str(len(error_case_list))] = error_case_list
    statis_dict["depend_" + str(len(depend_case_list))] = depend_case_list
    statis_dict["offline_" + str(len(offline_case_list))] = offline_case_list
    return statis_dict


def generate_report_with_statis_case(pro_name):
    """
    生成测试报告 ( Excel )
    :param pro_name:
    :return:
    """
    if pro_is_running(pro_name):
        return "当前项目正在运行中"
    else:
        statis_dict = statis_case(pro_name)
        now = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime(time.time()))
        current_report_name = "[API_report]" + pro_name + "[" + now + "].xls"
        pro_report_path = cfg.REPORTS_DIR + pro_name + "/"
        history_report_path = pro_report_path + "/history/"
        mkdir(history_report_path)
        current_report_file = history_report_path + current_report_name

        case_info_save_excel(excel_file=current_report_file, statis_dict=statis_dict)

        # 将最新报告替换../Reports/{{pro_name}}/下的[API_report]{{pro_name}}.xls
        res = os.system("cp " + current_report_file + " " + pro_report_path + " && "
                        "mv " + pro_report_path + current_report_name + " " + pro_report_path + "[API_report]" + pro_name + ".xls")
        if res != 0:
            log.error("测试报告替换操作有误！")
    return "生成完毕"


def case_info_save_excel(excel_file, statis_dict):
    """
    用例信息保存入 Excel
    :param excel_file:
    :param statis_dict:
    :return:
    """
    # 获取 excel head 数据
    field_name_dict = get_case_field_name()
    field_zn_list = list(field_name_dict.keys())
    field_cn_list = list(field_name_dict.values())

    # 获取 统计类别
    category_list = list(statis_dict.keys())

    # 将获取的数据存入excel中
    workbook = xlwt.Workbook(encoding='utf-8')
    for category_i, category in enumerate(category_list):
        category_name = category.split("_")[0]
        category_num = category.split("_")[1]
        # 添加 工作表
        sheet = workbook.add_sheet(category_name + "(" + category_num + ")", cell_overwrite_ok=True)

        # 工作表 添加 head 数据
        for cn_col_i in range(len(field_cn_list)):
            sheet.write(0, cn_col_i, field_cn_list[cn_col_i], set_style(name=u"宋体", bold=True, colour=0, size=300))
        for zn_col_i in range(len(field_zn_list)):
            sheet.write(1, zn_col_i, field_zn_list[zn_col_i], set_style(name=u"宋体", bold=True, colour=23, size=300))

        # 工作表 添加 数据
        case_list = statis_dict.get(category, [])
        for row_i, case_dict in enumerate(case_list):
            for col_i, value in enumerate(list(case_dict.values())):
                sheet.write(row_i + 2, col_i, value, set_style(name=u"宋体", bold=True, colour=0, size=300))

    workbook.save(excel_file)


if __name__ == "__main__":
    pass
    verify_result, excel_list = verify_excel_and_transfer_format(cfg.UPLOAD_CASE_FILE)
    print(verify_result)
    print(excel_list)

    # generate_report_with_statis_case("pro_demo_1")



