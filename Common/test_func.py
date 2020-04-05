# -*- coding:utf-8 -*-
from Common.com_func import send_mail, send_DD, log
from Config.pro_config import get_host_by_pro
from Tools.mongodb import MongodbUtils
from Config import config as cfg
from Tools.date_helper import get_current_iso_date
from TestBase.verify_interface import AcquireDependField, VerifyInterface
import re


def mongo_exception_send_DD(e, msg):
    """
    发现异常时钉钉通知
    :param e:
    :param msg:
    :return:
    """
    title = "[监控]'mongo'操作通知"
    text = "#### WEB自动化测试'mongo'操作错误\n\n****操作方式：" + msg + "****\n\n****错误原因：" + str(e) + "****"
    send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title=title, text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)


def test_interface(pro_name):
    """
    【 测 试 接 口 】（根据项目名）
    :param pro_name:
    :return:

    【 测 试 主 流 程 】
    1.获取上线的接口列表
    （1）上线的'依赖接口列表'
    （2）上线的'测试接口列表'
    2.[ 获 取 依 赖 字 段 值 ]
    （1）< 判断 > 是否需要依赖
    （2）若不需要，则 直接进入 [ 接 口 测 试 ]
    （3）若需要，则
        1）若'depend_interface_result_list'包含'success'，则 '依赖接口列表' 更新结果记录，并进入 [ 接 口 测 试 ]
        2）若'depend_interface_result_list'含有'error:依赖接口不存在'，则 '测试接口列表' 更新结果记录 -- STOP --
        3）若'depend_interface_result_list'其他情况，则 '依赖接口列表、测试接口列表' 更新结果记录 -- STOP --
    3.[ 验 证 接 口 ]
    （1）根据返回的'待更新字典'，更新 '测试接口列表' 中的数据
    """

    # 1.获取上线的接口列表
    # （1）上线的'依赖接口列表'（按照依赖等级顺序排列）
    # （2）上线的'测试接口列表'
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            depend_interface_list = pro_db.find({"case_status": True, "is_depend": True})
            test_interface_list = pro_db.find({"case_status": True, "is_depend": False})
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目上线接口列表")
            return
    depend_interface_list = list(depend_interface_list)
    test_interface_list = list(test_interface_list)

    # 2.[ 获 取 依 赖 字 段 值 ]
    adf = AcquireDependField(depend_interface_list=depend_interface_list, test_interface_list=test_interface_list)
    if adf.is_need_depend():
        adf.acquire()
    else:
        # 进入 [ 验 证 接 口 ]
        pass


     # 3.若不为空，则进入[ 获 取 依 赖 字 段 值 步 骤 ]
     #  根据返回值'test_result'判断后续步骤：
     # （1）若'test_result = error:依赖接口不存在'，则 '测试接口列表' 更新结果记录 -- STOP --
     # （2）若'test_result'不包含'success'，则 '依赖接口列表、测试接口列表' 更新结果记录 -- STOP --
     # （3）若'test_result'包含'success'，则 '依赖接口列表' 更新结果记录，并进入 [ 接 口 测 试 步 骤 ]


    # host = get_host_by_pro(pro_name)
    # depand_field_dict = {}  # 保存依赖字段的键值对
    # for index, test_case_dict in enumerate(test_case_dict_list):
    #     # for field, value in test_case_dict.items():
    #
    #     result_dict = VerifyInterface(interface_name=test_case_dict.get("interface_name"),
    #                                   interface_url=host + test_case_dict.get("interface_url"),
    #                                   request_method=test_case_dict.get("request_method"),
    #                                   request_header=test_case_dict.get("request_header"),
    #                                   request_params=test_case_dict.get("request_params"),
    #                                   verify_mode=test_case_dict.get("verify_mode"),
    #                                   compare_core_field_name_list=test_case_dict.get("compare_core_field_name_list"),
    #                                   expect_core_field_value_list=test_case_dict.get("expect_core_field_value_list"),
    #                                   expect_field_name_list=test_case_dict.get("expect_field_name_list"),
    #                                   depend_interface_list=test_case_dict.get("depend_interface_list"),
    #                                   depend_field_name_list=test_case_dict.get("depend_field_name_list")).verify()
    #
    #     # 更新用例
    #     result_dict["update_time"] = get_current_iso_date()
    #     pro_db.update({"_id": test_case_dict["_id"]}, {"$set": result_dict})


if __name__ == "__main__":
    test_interface("pro_demo_1")