# -*- coding:utf-8 -*-
import requests
import json
from Config.pro_config import get_host_by_pro
from Tools.mongodb import MongodbUtils
from Config import config as cfg
from bson.objectid import ObjectId
from Common.com_func import is_null, log
import re


class VerifyInterface(object):
    """
     【 验 证 接 口 步 骤 】
        0.若存在 '依赖接口名称：depend_interface'
         （1）无响应：记录 '测试结果：test_result' 字段值 < fail:依赖接口无响应 >
         （2）有相应（ http != 200 ）：记录 '测试结果：test_result' 字段值 < fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)" >
         （3）有响应（ http == 200 ）：继续
              1）捕获成功，则 记录 '依赖字段值：depend_field_value' 字段值，并修改 '请求参数：request_params' 字段值
              2）捕获失败，则 记录 '测试结果：test_result' 字段值 < fail:依赖字段捕获失败 >
        1.发送请求，验证response响应
         （1）无响应：记录 '测试结果：test_result' 字段值 < fail:测试接口无响应 >
         （2）有相应（ http != 200 ）：记录 '测试结果：test_result' 字段值 < fail:测试接口错误，http_code<500>,原因解析(Internal Server Error)" >
         （3）有响应（ http == 200 ）：继续
        2.记录 '响应信息：response_info' 字段值、获取'实际的相应字段列表'
        3.验证'待比较的关键字段名'列表
         （1）验证'待比较的关键字段名'列表是否都存在
         （2）获取'实际的关键字段值'列表
         （3）比较'关键字段值'列表
            记录 '响应字段列表比较结果：result_core_field_value' 字段值（ pass、fail、fail:关键字段名不存在）
        4.若'验证模式 = 2'，则还需要验证'待比较的响应字段列表'
            记录 '响应字段列表比较结果：result_field_name_list' 字段值（ pass、fail ）
        5.记录 '测试结果：test_result' 字段值
         （1）fail：关键字段比较失败
         （2）fail：关键字段比较失败，响应字段列表比较失败
         （3）fail：关键字段比较通过，响应字段列表比较失败
         （4）fail：关键字段比较失败，响应字段列表比较通过
         （5）pass：通过
        6.记录 '更新时间：update_time' 字段值
        7.数据库更新相应的'记录字段值值'

    """

    def __init__(self, interface_name, interface_url, request_method, request_header, request_params, verify_mode,
                 compare_core_field_name, expect_core_field_value, expect_field_name_list):
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
        # 响应信息
        self.response_info = ""
        self.response_dict = {}
        # 关键字段
        self.compare_core_field_name_list = compare_core_field_name
        self.expect_core_field_value_list = expect_core_field_value
        self.actual_core_field_value_list = []
        self.result_core_field_value = ""
        # 响应字段名列表
        self.expect_field_name_list = expect_field_name_list
        self.actual_field_name_list = []
        self.result_field_name_list = ""
        # 测试结果
        self.test_result = ""

    def verify(self):
        # 1.发送请求，验证response响应
        try:
            response = self.send_request()
        except Exception as e:
            log.error(e)
            self.test_result = "fail:测试接口无响应！"
            return self.test_result
        if response.status_code != 200:
            msg = re.search(r'<title>(.*?)</title>', response.text)
            self.test_result = "fail:测试接口错误,http_code<" + str(response.status_code) + ">,原因解析(" + msg.group(1) + ")"
            return self.test_result
        else:
            # 2.记录'响应信息：response_info'字段值、获取'实际的相应字段列表'
            self.response_info = response.text
            self.response_dict = json.loads(self.response_info)
            self.get_response_field_list()
            print(self.actual_field_name_list)
            # 3.验证'待比较的关键字段'列表
            self.verify_core_field_list()
            print(self.result_core_field_value)
            return "继续"

    def verify_core_field_list(self):
        """
        【 验证'待比较的关键字段名'列表 】
          1.验证'待比较的关键字段名'列表是否都存在
          2.获取'实际的关键字段值'列表
          3.比较'关键字段值'列表

        【 注 意 】
          关键字段值比较时，需要全部转换成'str'后再进行比较
          因为'mongo'中保存的都是string类型，接口返回的可能是int或bool类型
        :return:
        """
        # 验证'待比较的关键字段名'列表是否都存在
        for field in self.compare_core_field_name_list:
            if field not in self.actual_field_name_list:
                self.result_core_field_value = "fail:关键字段名不存在"
                return

        # 获取'实际的关键字段值'列表
        for field in self.compare_core_field_name_list:
            self.actual_core_field_value_list.append(self.response_dict[field])

        # 比较'关键字段值'列表
        for index, expect_value in enumerate(self.expect_core_field_value_list):
            if str(expect_value).strip() != str(self.actual_core_field_value_list[index]).strip():
                self.result_core_field_value = "fail"
                return
        self.result_core_field_value = "pass"
        return

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

    def get_response_field_list(self):
        """
        获取响应字段列表（去重）
        :return:
        """
        self.recur_params(self.response_info)
        self.actual_field_name_list = list(set(self.actual_field_name_list))

    def recur_params(self, response_info):
        """
        递归 捕获响应信息中的字段列表
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
                    continue


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

            # print(test_case_dict.get("interface_name"))
            # print(host+test_case_dict.get("interface_url"))
            # print(test_case_dict.get("request_method"))
            # print(test_case_dict.get("request_header"))
            # print(test_case_dict.get("request_params"))

            ri = VerifyInterface(interface_name=test_case_dict.get("interface_name"),
                                 interface_url=host+test_case_dict.get("interface_url"),
                                 request_method=test_case_dict.get("request_method"),
                                 request_header=test_case_dict.get("request_header"),
                                 request_params=test_case_dict.get("request_params"),
                                 verify_mode=test_case_dict.get("verify_mode"),
                                 compare_core_field_name=test_case_dict.get("compare_core_field_name"),
                                 expect_core_field_value=test_case_dict.get("expect_core_field_value"),
                                 expect_field_name_list=test_case_dict.get("expect_field_name_list"))
            print(ri.verify())



