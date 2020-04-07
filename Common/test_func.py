# -*- coding:utf-8 -*-
from Config.pro_config import get_host_by_pro
from Tools.mongodb import MongodbUtils
from Config import config as cfg
from Tools.date_helper import get_current_iso_date
from TestBase.verify_interface import VerifyInterface
from TestBase.acquire_depend import AcquireDependField
from Common.com_func import is_null, mongo_exception_send_DD


def test_interface(pro_name):
    """
    【 测 试 接 口 】（根据项目名）
    :param pro_name:
    :return:

    【 测 试 主 流 程 】
    1.获取上线的接口列表
    （1）上线的'依赖接口列表'
    （2）上线的'测试接口列表'
    2.判断是否存在 上线的'测试接口列表'
    3.获取依赖字段值
       < 判断 > 是否需要执行依赖：
     （1）若不需要 则 直接进入'验证接口'步骤
     （2）若需要 则获取依赖字段：
          1）若获取成功，则替换接口中的相应变量、进入'验证接口'步骤
          2）若获取失败，则不进行接口验证
          （ 备注：通过 'verify_flag' 标记进行控制 ）
    4.验证接口
    （1）执行测试，获取测试结果列表
    （2）更新测试结果
    """

    # 1.获取上线的接口列表
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        try:
            depend_interface_list = pro_db.find({"case_status": True, "is_depend": True})
            test_interface_list = pro_db.find({"case_status": True, "is_depend": False})
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目上线接口列表")
            return "mongo error"

    depend_interface_list = list(depend_interface_list)
    test_interface_list = list(test_interface_list)
    host = get_host_by_pro(pro_name)

    if is_null(test_interface_list):
        return "no online case"

    # 2.获取依赖字段值
    adf = AcquireDependField(pro_name=pro_name, host=host, depend_interface_list=depend_interface_list,
                             test_interface_list=test_interface_list)
    if adf.is_need_depend():
        test_interface_list = adf.acquire()

    # 3.验证接口
    if adf.verify_flag:
        # 执行测试，获取测试结果列表
        id_result_dict = {}   # {"_id":{"test_resuld":"success", "":""}, "_id":{}, }
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
            for _id, test_result in id_result_dict.items():
                test_result["update_time"] = update_time
                pro_db.update({"_id": _id}, {"$set": test_result})

    return "done"


if __name__ == "__main__":
    print(test_interface("pro_demo_1"))