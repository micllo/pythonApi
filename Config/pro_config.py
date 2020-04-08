# -*- coding:utf-8 -*-
from Config import global_var as gv


def get_pro_info(pro_name, host_name):
    """
    获取项目信息 （ host、run_status ）
    :param pro_name:
    :param host_name:
    :return:
    """
    host = None
    run_status = False
    if pro_name == "pro_demo_1":
        run_status = gv.RUN_STATUS_OF_PRO_DEMO_1
        if host_name == "7060":
            host = "http://127.0.0.1:7060/api_local"
    return run_status, host


def set_pro_run_status(pro_name, run_status):
    """
    设置项目运行状态
    :param pro_name:
    :param run_status:
    :return:
    """
    if pro_name == "pro_demo_1":
        gv.RUN_STATUS_OF_PRO_DEMO_1 = run_status
