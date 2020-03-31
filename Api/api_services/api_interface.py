# -*- coding: utf-8 -*-
from Api import *
import json
from Config.error_mapping import *
from Api.api_services.api_template import interface_template
from Api.api_services.api_calculate import *
from Common.com_func import is_null, log
from Tools.mongodb import MongoGridFS
from Config import config as cfg

"""
api 服务接口
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
####################################################################################
"""


# http://127.0.0.1:7060/api_local/API/index
@flask_app.route("/API/index", methods=["GET"])
def show_index():
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["api_addr"] = cfg.API_ADDR
    return render_template('index.html', tasks=result_dict)


# http://127.0.0.1:7060/api_local/API/get_project_case_list/pro_demo_1
@flask_app.route("/API/get_project_case_list/<pro_name>", methods=["GET"])
def get_test_case_list(pro_name):
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["pro_name"] = pro_name
    result_dict["test_case_list"] = get_test_case(pro_name)
    return render_template('project.html', tasks=result_dict)


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


@flask_app.route("/API/search_case/<pro_name>", methods=["GET"])
def search_case(pro_name):
    """
    搜到用例
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["test_case_list"] = get_case_search_result(request_args=request.args, pro_name=pro_name)
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


@flask_app.route("/API/get_case_by_id/<pro_name>", methods=["GET"])
def get_case(pro_name):
    """
    通过id获取用例（填充编辑弹层）
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["test_case"] = get_case_by_id(request_args=request.args, pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


