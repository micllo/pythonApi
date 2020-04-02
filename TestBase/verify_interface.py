# -*- coding:utf-8 -*-
import requests
import json
from Config.pro_config import get_host_by_pro
from Tools.mongodb import MongodbUtils
from Config import config as cfg
from bson.objectid import ObjectId
from Tools.date_helper import get_current_iso_date
from Common.com_func import is_null, log
import re


class VerifyInterface(object):
    """
     【 依 赖 接 口 验 证 步 骤 】
         1.检查'依赖接口名列表'是否都存在
            若不存在，则 记录 '测试结果：test_result' 字段值 < error:依赖接口不存在 >
         2.检查 测试接口的'request_params、request_header'中是否存在相应的'大写依赖字段名'
            比如：检查 测试接口的'request_params'中是否存在'TOKEN'字符串
            比如：检查 测试接口的'request_header'中是否存在'CONTENT_TYPE'字符串
            若不存在，则 记录 '测试结果：test_result' 字段值 < error:依赖字段名配置有误 >
         3.发送'依赖接口'请求
           （1）无响应：记录 '测试结果：test_result' 字段值 < fail:依赖接口无响应 >
           （2）有相应（ http != 200 ）：记录 '测试结果：test_result' 字段值 < fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)" >
           （3）有响应（ http == 200 ）：继续
         4.捕获 对应的'依赖接口请求'的响应参数中 对应的'小写的依赖字段名'的值
            比如：1-param-TOKEN -> 捕获第'1'个依赖接口响应参数中的'token'值
            比如：2-header-CONTENT_TYPE-> 捕获第'2'个依赖接口响应参数中的'content_type'值
            若获取不到，则记录 '测试结果：test_result' 字段值 < error:依赖字段值获取失败 >
         5.记录 '依赖字段值列表：depend_field_value_list' 字段值
         6.替换 测试接口的'request_params、request_header'中对应的'大写依赖字段名'

     【 测 试 接 口 验 证 步 骤 】
        0.判断是否需要执行依赖接口：若需要 则参考上面的 "依赖接口验证步骤"
        1.发送请求，验证response响应
         （1）无响应：记录 '测试结果：test_result' 字段值 < fail:测试接口无响应 >
         （2）有相应（ http != 200 ）：记录 '测试结果：test_result' 字段值 < fail:测试接口错误,http_code<500>,原因解析(Internal Server Error)" >
         （3）有响应（ http == 200 ）：继续
        2.记录 '响应信息：response_info' 字段值、获取'实际的响应字段列表、键值字典'
        3.验证'待比较的关键字段名'列表
         （1）验证'待比较的关键字段名'列表是否都存在
         （2）获取'实际的关键字段值'列表
         （3）比较'关键字段值'列表
            记录 '响应字段列表比较结果：result_core_field_value' 字段值（ pass、fail、fail:关键字段名不存在）
        4.若'验证模式 = 2'，则还需要验证'待比较的响应字段列表'
            记录 '响应字段列表比较结果：result_field_name_list' 字段值（ pass、fail ）
        5.记录 '测试结果：test_result' 字段值
         （1）success
         （2）fail:关键字段验证失败
         （3）fail:关键字段验证失败,响应字段列表验证失败
         （4）fail:关键字段验证通过,响应字段列表验证失败
         （5）fail:关键字段验证失败,响应字段列表验证通过
        6.获取 待数据库更新的字典
           retrun 待更新字典

        【 测试结果 test_result 包含内容 】
        01.success
        02.fail:关键字段验证失败
        03.fail:关键字段验证失败,响应字段列表验证失败
        04.fail:关键字段验证通过,响应字段列表验证失败
        05.fail:关键字段验证失败,响应字段列表验证通过
        06.fail:测试接口错误,http_code<500>,原因解析(Internal Server Error)
        07.fail:依赖接口无响应
        08.fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)
        09.error:依赖字段值获取失败
        10.error:依赖字段名配置有误
        11.error:依赖接口不存在

    """

    def __init__(self, interface_name, interface_url, request_method, request_header, request_params, verify_mode,
                 compare_core_field_name_list, expect_core_field_value_list, expect_field_name_list,
                 depend_interface_list, depend_field_name_list):
        # 请求相关
        self.interface_name = interface_name
        self.interface_url = interface_url
        self.request_method = request_method
        if request_header:
            self.request_header = eval(request_header)  # string -> dict
        else:  # ""
            self.request_header = request_header
        if request_params and request_params.startswith("{"):
            self.request_params = json.dumps(eval(request_params))  # string -> dict -> json
        else:  # "" 或 '?xx=xx'
            self.request_params = request_params
        # 验证模式
        self.verify_mode = verify_mode
        # 依赖数据
        self.depend_interface_list = depend_interface_list
        self.depend_field_name_list = depend_field_name_list
        self.depend_field_value_list = []
        # 响应信息
        self.response_info = ""
        self.response_dict = {}
        # 关键字段
        self.compare_core_field_name_list = compare_core_field_name_list
        self.expect_core_field_value_list = expect_core_field_value_list
        self.actual_core_field_value_list = []
        self.result_core_field_value = ""
        # 响应字段名列表
        self.actual_field_dict = {}  # 实际响应信息中的 field_value 字典（若有重复 则取最后一个）
        self.expect_field_name_list = expect_field_name_list
        self.actual_field_name_list = []
        self.result_field_name_list = ""
        # 测试结果
        self.test_result = ""
        # 待数据库更新的字典
        self.update_result_dict = {}

    def verify(self):

        # 1.发送请求，验证response响应
        try:
            response = self.send_request()
        except Exception as e:
            log.error(e)
            self.test_result = "fail:测试接口无响应！"
            # 获取 待数据库更新的字典
            self.get_mongo_update_result_dict()
            print(self.update_result_dict)
            return self.update_result_dict

        if response.status_code != 200:
            msg = re.search(r'<title>(.*?)</title>', response.text)
            self.test_result = "fail:测试接口错误,http_code<" + str(response.status_code) + ">,原因解析(" + msg.group(1) + ")"
        else:
            # 2.记录'响应信息：response_info'字段值、获取'实际的响应字段列表、键值字典'
            self.response_info = response.text
            self.response_dict = json.loads(self.response_info)
            self.get_response_field_list_and_dict()

            # 3.验证'待比较的关键字段'列表
            self.verify_core_field_list()

            # 4.若'验证模式 = 2'，则验证'待比较的响应字段列表'
            self.verify_mode == 2 and self.verify_response_field_name_list()

            # 5.记录 '测试结果：test_result' 字段值
            self.get_test_result()

        # 获取 待数据库更新的字典
        self.get_mongo_update_result_dict()
        print(self.update_result_dict)
        return self.update_result_dict

    def send_request(self):
        if self.request_method == "GET":
            response_info = requests.get(url=self.interface_url+self.request_params, headers=self.request_header)
        elif self.request_method == "POST":
            response_info = requests.post(url=self.interface_url, data=self.request_params, headers=self.request_header)
        elif self.request_method == "PUT":
            response_info = requests.put(url=self.interface_url, data=self.request_params, headers=self.request_header)
        else:
            response_info = requests.delete(url=self.interface_url, data=self.request_params, headers=self.request_header)
        return response_info

    def get_response_field_list_and_dict(self):
        """
        获取
        1.响应信息中的所有 field 列表    （ self.actual_field_name_list ）（去重）
        2.响应信息中的 field_value 字典 （ self.actual_field_dict ）
        :return:
        """
        self.recur_params(self.response_info)
        self.actual_field_name_list = list(set(self.actual_field_name_list))

    def recur_params(self, response_info):
        """
        递归 捕获
        1.响应信息中的所有 field 列表    （ self.actual_field_name_list ）
        2.响应信息中的 field_value 字典 （ self.actual_field_dict ）
        （1）若 value 为 dict 类型，则该 field_value 不获取
        （2）若 value 为 list 类型，则该 field_value 不获取
        （3）若 存在相同的 field 名称， 则获取最后一个 field_value
        :return:
        """
        # 若是字符串类型，且能被转换成字典
        if isinstance(response_info, str) and response_info.startswith("{"):
            response_info_dict = json.loads(response_info)
            self.recur_params(response_info_dict)
        elif isinstance(response_info, dict):
            for field, value in response_info.items():
                self.actual_field_name_list.append(field)
                if isinstance(value, list):
                    for field in value:
                        self.recur_params(field)
                elif isinstance(value, dict):
                    self.recur_params(value)
                else:
                    self.actual_field_dict[field] = value

    def verify_core_field_list(self):
        """
        【 验证'待比较的关键字段名'列表 】
          1.验证'待比较的关键字段名'列表是否都存在
          2.获取'实际的关键字段值'列表
          3.比较'关键字段值'列表

        【 注 意 】
          接口返回的字段 可能是int或bool类型，所以需要将其全部转换成str后，再进行比较和保存mongo
        :return:
        """
        # 验证'待比较的关键字段名'列表是否都存在
        for field in self.compare_core_field_name_list:
            if field not in self.actual_field_dict.keys():
                self.result_core_field_value = "fail:关键字段名不存在"
                return

        # 获取'实际的关键字段值'列表
        for field in self.compare_core_field_name_list:
            self.actual_core_field_value_list.append(str(self.actual_field_dict[field]))

        # 比较'关键字段值'列表
        for index, expect_value in enumerate(self.expect_core_field_value_list):
            if str(expect_value).strip() != self.actual_core_field_value_list[index].strip():
                self.result_core_field_value = "fail"
                return
        self.result_core_field_value = "pass"
        return

    def verify_response_field_name_list(self):
        """
        【 验证'待比较的响应字段列表' 】
        1.记录'不存在的字段名列表'
        2.若'不存在的字段名列表'有值，则记录结果为'fail'
          若'不存在的字段名列表'为空，则记录结果为'pass'
        :return:
        """
        non_existent_field_name_list = [field for field in self.expect_field_name_list if field not in self.actual_field_name_list]
        self.result_field_name_list = non_existent_field_name_list and "fail" or "pass"

    def get_test_result(self):
        """
        【 获 取 测 试 结 果 】
        1.success
        2.fail:关键字段验证失败
        3.fail:关键字段验证失败,响应字段列表验证失败
        4.fail:关键字段验证通过,响应字段列表验证失败
        5.fail:关键字段验证失败,响应字段列表验证通过
        :return:
        """
        if self.verify_mode == 1:
            self.test_result = self.result_core_field_value == "pass" and "success" or "fail:关键字段验证失败"
        else:
            if self.result_core_field_value != "pass" and self.result_field_name_list != "pass":
                self.test_result = "fail:关键字段验证失败,响应字段列表验证失败"
            elif self.result_core_field_value == "pass" and self.result_field_name_list != "pass":
                self.test_result = "fail:关键字段验证通过,响应字段列表验证失败"
            elif self.result_core_field_value != "pass" and self.result_field_name_list == "pass":
                self.test_result = "fail:关键字段验证失败,响应字段列表验证通过"
            else:
                self.test_result = "success"

    def get_mongo_update_result_dict(self):
        """
        【 获取 待数据库更新的字典 】
        """
        self.update_result_dict = {"response_info": self.response_info,
                                   "depend_field_value_list": self.depend_field_value_list,
                                   "actual_core_field_value_list": self.actual_core_field_value_list,
                                   "result_core_field_value": self.result_core_field_value,
                                   "result_field_name_list": self.result_field_name_list,
                                   "test_result": self.test_result}


if __name__ == "__main__":

    # http://127.0.0.1:7060/api_local/test/test_get_request?test_str=接口自动化测试&test_int=5&test_bool=True
    # http://127.0.0.1:7060/api_local/test/test_post_request   {"test_str":"post测试","test_int":5,"test_bool":"true"}

    # interface_name = "测试带参数的get请求"
    # interface_url = "http://127.0.0.1:7060/api_local/test/test_get_request"
    # request_method = "GET"
    # request_header = ""
    # request_params = "?test_str=接口自动化测试&test_int=5&test_bool=True"

    # interface_name = "测试post请求"
    # interface_url = "http://127.0.0.1:7060/api_local/test/test_post_request"
    # request_method = "POST"
    # request_header = "{\"Content-Type\": \"application/json\"}"
    # request_params = "{\"test_str\":\"post测试\",\"test_int\":5,\"test_bool\":\"true\"}"
    #
    # ri = VerifyInterface(interface_name=interface_name, interface_url=interface_url, request_method=request_method,
    #                       request_header=request_header, request_params=request_params)
    # respone = ri.send_request()
    # print(respone)
    # print(respone.status_code)
    # print(respone.text)

    pro_name = "pro_demo_1"
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name) as pro_db:
        test_case_dict_list = pro_db.find({"case_status": True})
        host = get_host_by_pro(pro_name)
        for index, test_case_dict in enumerate(test_case_dict_list):
            # for field, value in test_case_dict.items():

            result_dict = VerifyInterface(interface_name=test_case_dict.get("interface_name"),
                                          interface_url=host+test_case_dict.get("interface_url"),
                                          request_method=test_case_dict.get("request_method"),
                                          request_header=test_case_dict.get("request_header"),
                                          request_params=test_case_dict.get("request_params"),
                                          verify_mode=test_case_dict.get("verify_mode"),
                                          compare_core_field_name_list=test_case_dict.get("compare_core_field_name_list"),
                                          expect_core_field_value_list=test_case_dict.get("expect_core_field_value_list"),
                                          expect_field_name_list=test_case_dict.get("expect_field_name_list"),
                                          depend_interface_list=test_case_dict.get("depend_interface_list"),
                                          depend_field_name_list=test_case_dict.get("depend_field_name_list")).verify()

            # 更新用例
            result_dict["update_time"] = get_current_iso_date()
            pro_db.update({"_id": test_case_dict["_id"]}, {"$set": result_dict})


