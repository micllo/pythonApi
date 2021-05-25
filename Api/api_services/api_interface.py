# -*- coding: utf-8 -*-
from Api import *
from flask import render_template, request
import json
from Config.error_mapping import *
from Api.api_services.api_template import interface_template
from Api.api_services.api_calculate import *
from Common.com_func import is_null
from Env import env_config as cfg
from Config.pro_config import pro_name_list

"""
api 服务接口
"""


# http://127.0.0.1:7060/api_local/API/index
@flask_app.route("/API/index", methods=["GET"])
def show_index():
    """   跳转 首页   """
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["api_addr"] = cfg.API_ADDR
    result_dict["pro_name_list"] = pro_name_list
    result_dict["pro_num"] = len(pro_name_list)
    return render_template('index.html', tasks=result_dict)


# http://127.0.0.1:7060/api_local/API/get_project_case_info/pro_demo_1
@flask_app.route("/API/get_project_case_info/<pro_name>", methods=["GET"])
def get_test_case_info(pro_name):
    """   跳转 用例页面   """
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["pro_name"] = pro_name
    result_dict["host_list"], result_dict["global_variable_list"], result_dict["cron_status"] = get_config_info(pro_name)
    result_dict["test_case_list"], result_dict["is_run"] = get_test_case(pro_name=pro_name, db_tag="_case")
    result_dict["statist_data"] = get_statist_data_for_case(pro_name)
    result_dict["current_report_url"] = cfg.BASE_REPORT_PATH + pro_name + "/[API_report]" + pro_name + ".xls"
    result_dict["history_report_path"] = cfg.BASE_REPORT_PATH + pro_name + "/history/"
    return render_template('project.html', tasks=result_dict)


# http://127.0.0.1:7060/api_local/API/get_test_report/pro_demo_1
@flask_app.route("/API/get_test_report/<pro_name>", methods=["GET"])
def get_test_report(pro_name):
    """   跳转 测试报告   """
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["pro_name"] = pro_name
    test_time_list = get_test_time_list(pro_name)
    result_dict["test_time_list"] = test_time_list
    result_dict["host_list"], result_dict["global_variable_list"], result_dict["cron_status"] = get_config_info(pro_name)
    result_dict["test_case_list"], result_dict["is_run"] = get_test_case(pro_name=pro_name, db_tag="_result", last_test_time=test_time_list[0])
    result_dict["statist_data"] = get_statist_data_for_result(pro_name, test_time_list[0])
    return render_template('report.html', tasks=result_dict)


@flask_app.route("/API/query_statist_data/<pro_name>", methods=["GET"])
def query_statist_data(pro_name):
    """
    获取统计数据
    :param pro_name
    :param
    :return:
    """
    res_info = dict()
    params = request.args
    test_time = params.get("test_time", "")  # str
    res_info["statist_data"] = get_statist_data_for_result(pro_name, test_time)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/import_action/<pro_name>/<import_method>", methods=["POST"])
def import_action(pro_name, import_method):
    """
    导入用例操作
    :param pro_name
    :param import_method: 导入方式（批量新增、全部替换、批量替换）
    :return:
    """
    # 获取request中的upload文件
    upload_file = request.files.get("file", None)
    res_info = case_import_action(pro_name, upload_file, import_method)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/generate_report/<pro_name>", methods=["GET"])
def generate_report(pro_name):
    """
    生成报告
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["msg"] = generate_report_with_statis_case(pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/get_run_status/<pro_name>", methods=["GET"])
def get_run_status(pro_name):
    """
    获取运行状态
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["is_run"] = pro_is_running(pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/run_test/<pro_name>", methods=["POST"])
def run_test(pro_name):
    """
    运行测试
    :param pro_name
    :return:
    """
    res_info = dict()
    host = request.json.get("host", "").strip()
    res_info["msg"] = run_test_by_pro(host=host, pro_name=pro_name, run_type="manual")
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/set_case_status_all/<pro_name>/<case_status>", methods=["GET"])
def set_case_status_all(pro_name, case_status):
    """
    设置整个项目的'测试用例'的'状态'(上下线)
    :param pro_name:
    :param case_status:
    :return:
    """
    res_info = dict()
    if is_null(pro_name) or is_null(case_status):
        res_info["msg"] = PARAMS_NOT_NONE
    elif pro_is_running(pro_name):
        res_info["msg"] = CURRENT_IS_RUNNING
    else:
        if case_status in [True, False, "false", "FALSE", "TRUE", "true"]:
            case_status = case_status in [True, "TRUE", "true"] and True or False
            res_info["msg"] = update_case_status_all(pro_name, case_status)
        else:
            res_info["msg"] = REQUEST_ARGS_WRONG
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/set_case_status/<pro_name>/<_id>", methods=["GET"])
def set_case_status(pro_name, _id):
    """
    设置某个'测试用例'的'状态'(上下线)
    :param pro_name:
    :param _id:
    :return:
    """
    new_case_status = None
    if is_null(pro_name) or is_null(_id):
        msg = PARAMS_NOT_NONE
    elif pro_is_running(pro_name):
        msg = CURRENT_IS_RUNNING
    else:
        new_case_status = update_case_status(pro_name, _id)
        msg = new_case_status == "mongo error" and MONGO_CONNECT_FAIL or UPDATE_SUCCESS
    re_dict = interface_template(msg, {"pro_name": pro_name, "_id": _id,
                                       "new_case_status": new_case_status})
    return json.dumps(re_dict, ensure_ascii=False)


@flask_app.route("/API/set_cron_status/<pro_name>", methods=["GET"])
def set_cron_status(pro_name):
    """
    修改定时任务状态
    :param pro_name:
    :return:
    """
    new_cron_status = None
    if is_null(pro_name):
        msg = PARAMS_NOT_NONE
    else:
        new_cron_status = update_cron_status(pro_name)
        msg = new_cron_status == "mongo error" and MONGO_CONNECT_FAIL or UPDATE_SUCCESS
    re_dict = interface_template(msg, {"pro_name": pro_name, "new_case_status": new_cron_status})
    return json.dumps(re_dict, ensure_ascii=False)


@flask_app.route("/API/stop_run_status/<pro_name>", methods=["GET"])
def stop_run_status(pro_name):
    """
    停止用例运行状态
    :param pro_name
    :return:
    """
    res_info = dict()
    set_pro_run_status(pro_name=pro_name, run_status=False)
    res_info["msg"] = "停止成功"
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/search_case/<pro_name>/<db_tag>", methods=["GET"])
def search_case(pro_name, db_tag):
    """
    搜到用例
    :param pro_name
    :param db_tag:  _case | _result
    :return:
    """
    res_info = dict()
    res_info["test_case_list"], res_info["case_num"], res_info["is_run"] = \
        get_case_search_result(request_args=request.args, pro_name=pro_name, db_tag=db_tag)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/config_variable/<pro_name>/<config_type>", methods=["POST"])
def config_variable(pro_name, config_type):
    """
    配置变量（ HOST | 全局变量 ） （ 添加 | 编辑 ）
    :param pro_name
    :param config_type：host | global_variable
    :return:
    """
    res_info = dict()
    res_info["msg"] = get_config_result(request_json=request.json, pro_name=pro_name, config_type=config_type)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/check_depend_variable/<pro_name>", methods=["GET"])
def check_depend_variable(pro_name):
    """
    检测依赖变量 是否配置正确
    :param pro_name:
    :return:
    """
    res_info = dict()
    res_info["msg"] = get_check_depend_variable_result(pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/check_global_variable/<pro_name>", methods=["GET"])
def check_global_variable(pro_name):
    """
    检测全局变量 是否配置正确
    :param pro_name:
    :return:
    """
    res_info = dict()
    res_info["msg"], global_variable_dict = get_check_global_variable_result(pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/operation_case/<mode>/<pro_name>", methods=["POST"])
def operation_case(pro_name, mode):
    """
    添加 | 编辑 用例
    :param pro_name
    :param mode  添加 add | 编辑 edit
    :return:
    """
    res_info = dict()
    res_info["msg"] = get_case_operation_result(request_json=request.json, pro_name=pro_name, mode=mode)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/del_config/<pro_name>", methods=["DELETE"])
def del_config(pro_name):
    """
    删除配置 （ HOST | 全局变量 ）
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["msg"] = get_config_del_result(request_json=request.json, pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/del_case/<pro_name>", methods=["DELETE"])
def del_case(pro_name):
    """
    删除用例
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["msg"] = get_case_del_result(request_json=request.json, pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/get_current_case/<pro_name>", methods=["POST"])
def get_current_case(pro_name):
    """
    获取已有用例（填充新增弹层）
    :return:
    """
    res_info = dict()
    res_info["test_case"] = get_case_by_name(request_json=request.json, pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/API/get_case_by_id/<pro_name>/<db_tag>", methods=["GET"])
def get_case(pro_name, db_tag):
    """
    通过id获取用例（填充编辑弹层）
    :param pro_name
    :param db_tag:  _case | _result
    :return:
    """
    res_info = dict()
    res_info["test_case"] = get_case_by_id(request_args=request.args, pro_name=pro_name, db_tag=db_tag)
    return json.dumps(res_info, ensure_ascii=False)


"""
#################################【 以 下 为 测 试 接 口（ 供 debug 使 用 ） 】###########################################
"""

"""
  【 不 需 要 依 赖 的 接 口 】
"""


# http://127.0.0.1:7060/api_local/test/test_get_request_no_params
@flask_app.route("/test/test_get_request_no_params", methods=["GET"])
def test_get_request_no_params():
    result_dict = {"pro_name": "pro_demo_1", "browser_name": "Chrome"}
    msg = CASE_RUNING
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


# http://127.0.0.1:7060/api_local/test/test_get_request?test_str=接口自动化测试&test_int=5&test_bool=True
@flask_app.route("/test/test_get_request", methods=["GET"])
def test_get_request():
    params = request.args
    test_str = params.get("test_str", "")  # str
    test_int = params.get("test_int", "")  # str
    test_bool = params.get("test_bool", "")  # str
    result_dict = {"test_str": test_str, "test_int": test_int, "test_bool": test_bool}
    msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


# http://127.0.0.1:7060/api_local/test/test_post_request
@flask_app.route("/test/test_post_request", methods=["POST"])
def test_post_request():
    params = request.json
    test_str = params.get("test_str")  # str
    test_int = params.get("test_int")   # int
    test_bool = params.get("test_bool")  # str
    response_list = ["list_str", 5, True]
    response_dict = {"name": "Messi", "age": 32, "sex": True}
    response_list_dict = [{"name": "Henry", "age": 43}, {"name": "Ronaldo", "age": 40}]
    result_dict = {"test_str": test_str, "test_int": test_int, "test_bool": test_bool, "response_list": response_list,
                   "response_dict": response_dict, "response_list_dict": response_list_dict}
    msg = SYNC_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


"""
    【 依 赖 接 口 逻 辑 】
    1.获取图片：  依赖接口 < 登录 >         依赖字段 < token >
    2.依赖get：  依赖接口 < 登录,获取图片 >  依赖字段 < token,image_id >
    3.依赖post： 依赖接口 < 登录,获取图片 >  依赖字段 < token,image_id,Content_Type >
"""


# http://127.0.0.1:7060/api_local/test/login
@flask_app.route("/test/login", methods=["POST"])
def test_login():
    """
    登录接口 - < 入参格式：json >
     返回依赖参数
      1.token
      2.Content_Type
    :return:
    """
    if request.content_type != "application/json":
        result_dict = {"content_type": request.content_type}
        msg = CONTENT_TYPE_WRONT
    else:
        params = request.json
        name = params.get("name")  # str
        passwd = params.get("passwd")   # int
        result_dict = {"name": name, "passwd": passwd, "token": "tokenid_112233445566", "content-type": "application/json"}
        msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


# http://127.0.0.1:7060/api_local/test/get_image?token=123456
@flask_app.route("/test/get_image", methods=["GET"])
def test_get_image():
    """
    获取图片接口
     需要的依赖参数
      1.token
     返回的依赖参数
      1.image_id
    :return:
    """
    params = request.args
    image_id = params.get("image_id", "1234567890")
    token = params.get("token", "")
    if token == "tokenid_112233445566":
        result_dict = {"image_id": image_id, "token": token}
    else:
        result_dict = {"token": token}
    msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


# http://127.0.0.1:7060/api_local/test/depend_get?image_id=xxxx&token=xxxx
@flask_app.route("/test/depend_get", methods=["GET"])
def test_depend_get():
    """
    依赖get接口
     需要的依赖参数
      1.token
      2.image_id
    :return:
    """
    params = request.args
    image_id = params.get("image_id", "")
    token = params.get("token", "")
    result_dict = {"image_id": image_id, "token": token, "info": "messi_get"}
    msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


# http://127.0.0.1:7060/api_local/test/depend_get2/xxxxxxxx?token=xxxx
@flask_app.route("/test/depend_get2/<image_id>", methods=["GET"])
def test_depend_get2(image_id):
    """
    依赖get接口2
     需要的依赖参数
      1.image_id
    :return:
    """
    params = request.args
    token = params.get("token", "")
    result_dict = {"image_id": image_id, "token": token, "info": "messi_get2"}
    msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


# http://127.0.0.1:7060/api_local/test/depend_post
@flask_app.route("/test/depend_post", methods=["POST"])
def test_depend_post():
    """
    依赖post接口
     需要的依赖参数
      1.token
      2.image_id
      3.Content_Type
    :return:
    """
    params = request.json
    image_id = params.get("image_id", "")
    token = params.get("token", "")
    result_dict = {"image_id": image_id, "token": token, "info": "messi_post"}
    msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


@flask_app.route("/test/form_post", methods=["POST", "PUT", "DELETE"])
def test_form_post():
    """
    form_post接口- < 入参格式：form >
    :return:
    """
    if request.content_type != "application/x-www-form-urlencoded":
        result_dict = {"content_type": request.content_type}
        msg = CONTENT_TYPE_WRONT
    else:
        params = request.form
        form_name = params.get("form_name", "")
        result_dict = {"form_name": form_name}
        msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)


@flask_app.route("/test/json_post", methods=["POST", "PUT", "DELETE"])
def test_json_post():
    """
    json_post接口- < 入参格式：json >
    :return:
    """
    if request.content_type != "application/json":
        result_dict = {"content_type": request.content_type}
        msg = CONTENT_TYPE_WRONT
    else:
        params = request.json
        json_name = params.get("json_name", "")
        result_dict = {"json_name": json_name}
        msg = REQUEST_SUCCESS
    re_dict = interface_template(msg, result_dict)
    return json.dumps(re_dict, ensure_ascii=False)

