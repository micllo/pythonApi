# -*- coding: utf-8 -*-
from Api import *
import json
from Config.error_mapping import *
from Api.api_services.api_template import interface_template
from Api.api_services.api_calculate import *
from Common.com_func import is_null, log
from Tools.mongodb import MongoGridFS
from Config import config as cfg
from Config import global_var as gv

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
    test_str = params.get("test_str")  # str
    test_int = params.get("test_int")  # str
    test_bool = params.get("test_bool")  # str
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
    result_dict["test_case_list"] = []
    return render_template('project.html', tasks=result_dict)


@flask_app.route("/API/import_action/<import_method>", methods=["POST"])
def import_action(import_method):
    """
    导入用例操作
    :param import_method: 导入方式（批量新增、全部替换、批量替换）
    :return:
    """
    # 获取request中的upload文件
    upload_file = request.files.get("file", None)
    res_info = case_import_action(upload_file, import_method)
    return json.dumps(res_info, ensure_ascii=False)


# @flask_app.route("/WEB/sync_run_case/<pro_name>", methods=["POST"])
# def run_case(pro_name):
#     """
#     同时执行不同的用例 (开启线程执行，直接返回接口结果)
#     :param pro_name:
#     :return:
#
#     browser_name: Chrome、Firefox
#     thread_num: 线程数
#     """
#     params = request.json
#     browser_name = params.get("browser_name") if params.get("browser_name") else None
#     thread_num = params.get("thread_num") if params.get("thread_num") else None
#     if not pro_exist(pro_name):
#         msg = PRO_NOT_EXIST
#     elif is_null(browser_name) or is_null(thread_num):
#         msg = PARAMS_NOT_NONE
#     elif browser_name not in ["Chrome", "Firefox"]:
#         msg = BROWSER_NAME_ERROR
#     elif thread_num not in range(1, 6):  # 线程数量范围要控制在1~5之间
#         msg = THREAD_NUM_ERROR
#     else:
#         run_flag = is_exist_start_case(pro_name)
#         if run_flag == "mongo error":
#             msg = MONGO_CONNECT_FAIL
#         else:
#             if run_flag:
#                 msg = EXIST_RUNNING_CASE
#             elif is_exist_online_case(pro_name):
#                 sync_run_case(pro_name, browser_name, thread_num)
#                 msg = CASE_RUNING
#             else:
#                 msg = NO_ONLINE_CASE
#     result_dict = {"pro_name": pro_name, "browser_name": browser_name, "thread_num": thread_num}
#     re_dict = interface_template(msg, result_dict)
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/get_img/5e61152ff0dd77751382563f
# @flask_app.route("/WEB/get_img/<file_id>", methods=["GET"])
# def get_screenshot_img(file_id):
#     """
#     获取截屏图片
#     :param file_id:
#     :return: 1.获取成功、2.找不到该文件、3.mongo连接不上
#     """
#     if is_null(file_id):
#         msg = PARAMS_NOT_NONE
#         img_base64 = ""
#     else:
#         mgf = MongoGridFS()
#         img_base64 = mgf.get_base64_by_id(file_id)
#         if is_null(img_base64):
#             msg = MONGO_CONNECT_FAIL
#         elif img_base64 == "no such file":
#             msg = NO_SUCH_FILE
#         else:
#             msg = REQUEST_SUCCESS
#             # response = make_response(img_base64)
#             # response.headers.set('Content-Type', 'image/png')
#             # return response
#     re_dict = interface_template(msg, {"file_id": file_id, "img_base64": img_base64})
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/sync_case_list/pro_demo_1
# @flask_app.route("/WEB/sync_case_list/<pro_name>", methods=["GET"])
# def sync_case_list(pro_name):
#     """
#     将某项目的所有测试用例同步入mongo库中，默认状态为'下线'
#     :param pro_name:
#     :return:
#     """
#     if is_null(pro_name):
#         msg = PARAMS_NOT_NONE
#     else:
#         insert_result = case_import_mongo(pro_name)
#         if insert_result == "mongo error":
#             msg = MONGO_CONNECT_FAIL
#         elif insert_result == "no such pro":
#             msg = NO_SUCH_PRO
#         else:
#             msg = SYNC_SUCCESS
#     re_dict = interface_template(msg, {"pro_name": pro_name})
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/set_case_status/pro_demo_1/test_02
# @flask_app.route("/WEB/set_case_status/<pro_name>/<test_method_name>", methods=["GET"])
# def set_case_status(pro_name, test_method_name):
#     """
#     设置某个'测试用例'的'状态'(上下线)
#     :param pro_name:
#     :param test_method_name:
#     :return:
#     """
#     new_case_status = None
#     if is_null(pro_name) or is_null(test_method_name):
#         msg = PARAMS_NOT_NONE
#     else:
#         new_case_status = update_case_status(pro_name, test_method_name)
#         msg = new_case_status == "mongo error" and MONGO_CONNECT_FAIL or UPDATE_SUCCESS
#     re_dict = interface_template(msg, {"pro_name": pro_name, "test_method_name": test_method_name,
#                                        "new_case_status": new_case_status})
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/set_case_status_all/pro_demo_1/false
# @flask_app.route("/WEB/set_case_status_all/<pro_name>/<case_status>", methods=["GET"])
# def set_case_status_all(pro_name, case_status):
#     """
#     设置整个项目的'测试用例'的'状态'(上下线)
#     :param pro_name:
#     :param case_status:
#     :return:
#     """
#     test_method_name_list = []
#     if is_null(pro_name) or is_null(case_status):
#         msg = PARAMS_NOT_NONE
#     else:
#         if case_status in [True, False, "false", "FALSE", "TRUE", "true"]:
#             case_status = case_status in [True, "TRUE", "true"] and True or False
#             res = update_case_status_all(pro_name, case_status)
#             if res == "mongo error":
#                 msg = MONGO_CONNECT_FAIL
#             else:
#                 msg = UPDATE_SUCCESS
#                 test_method_name_list = res
#         else:
#             msg = REQUEST_ARGS_WRONG
#     re_dict = interface_template(msg, {"pro_name": pro_name, "case_status": case_status,
#                                        "test_method_name_list": test_method_name_list})
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/stop_run_status/pro_demo_1
# @flask_app.route("/WEB/stop_run_status/<pro_name>", methods=["GET"])
# def stop_run_status(pro_name):
#     """
#     强行修改用例运行状态 -> 停止
#     :param pro_name:
#     :return:
#     """
#     if is_null(pro_name):
#         msg = PARAMS_NOT_NONE
#     else:
#         insert_result = stop_case_run_status(pro_name)
#         if insert_result == "mongo error":
#             msg = MONGO_CONNECT_FAIL
#         else:
#             msg = STOP_SUCCESS
#     re_dict = interface_template(msg, {"pro_name": pro_name})
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/refresh_run_progress/pro_demo_1
# @flask_app.route("/WEB/refresh_run_progress/<pro_name>", methods=["GET"])
# def refresh_run_progress(pro_name):
#     """
#     刷新执行用例进度
#     :param pro_name:
#     :return:
#     """
#     if is_null(pro_name):
#         msg = PARAMS_NOT_NONE
#     else:
#         progress_info = get_progress_info(pro_name)
#         if progress_info == "mongo error":
#             msg = MONGO_CONNECT_FAIL
#         else:
#             msg = REQUEST_SUCCESS
#     re_dict = interface_template(msg, {"pro_name": pro_name, "progress_info": progress_info})
#     return json.dumps(re_dict, ensure_ascii=False)
#
#
# # http://127.0.0.1:8070/api_local/WEB/refresh_case_run_status/pro_demo_1
# @flask_app.route("/WEB/refresh_case_run_status/<pro_name>", methods=["GET"])
# def refresh_case_run_status(pro_name):
#     """
#     刷新用例运行状态
#     :param pro_name:
#     :return:
#     """
#     if is_null(pro_name):
#         msg = PARAMS_NOT_NONE
#     else:
#         case_run_status_list = get_case_run_status(pro_name)
#         if case_run_status_list == "mongo error":
#             msg = MONGO_CONNECT_FAIL
#         else:
#             msg = REQUEST_SUCCESS
#     re_dict = interface_template(msg, {"pro_name": pro_name, "case_run_status_list": case_run_status_list})
#     return json.dumps(re_dict, ensure_ascii=False)
#
