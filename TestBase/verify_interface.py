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


class AcquireDependField(object):
    """
     【 获 取 依 赖 字 段 值 】
     0.获取'测试接口列表'中的'参数依赖字段名列表'（去重）( 接口地址、请求头文件、请求参数 )
       < 根据 '参数依赖字段名列表' 判断是否需要 执行依赖接口 >
     1.判断是否存在依赖接口
      （1）若不存在，则'整体记录' < error:依赖接口不存在 >
      （2）若存在，则 继续
     2.获取'依赖接口列表'中的'依赖字段值名列表'
     3.判断 '测试接口列表'中的依赖字段是否都包含在'依赖接口列表'中的依赖字段里面
      （1）若存在不包含的情况，则'整体记录' < error:依赖字段名配置有误 >
      （2）若全包含，则 继续
     4.发送'依赖接口'请求(先按照依赖等级顺序排列),捕获'依赖字段值'
      （1）无响应：'分开记录' < fail:依赖接口无响应 >
      （2）有相应（ http != 200 ）：'分开记录'< fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)" >
      （3）有响应（ http == 200 ）：则 '分开记录'< success:依赖通过 >
     5.判断'依赖字段值'是否全部都获取到
      （1）否，则 '整体记录' < error:依赖字段值没有全部获取到 >
      （2）是，替换'测试接口'中的'依赖字段变量'
     7.return：depend_interface_result_list, depend_field_dict


     依赖接口本身也需要依赖字段




       < 依 赖 接 口 test_result >
        01.success:依赖通过
        02.fail:依赖接口无响应
        03.fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)
        04.error:依赖字段值没有全部获取到
        05.error:依赖字段名配置有误

        [ 备 注 ]
        1.'error:依赖接口不存在'不记录在'依赖接口 test_result'中，而是记录在'测试接口 test_result'中
        2.依赖接口列表 整体记录 的 'test_result'
        （1）error:依赖接口不存在
        （2）error:依赖字段名配置有误
        （3）error:依赖字段值没有全部获取到
        3.依赖接口列表 分开记录 的 'test_result':
        （1）success:依赖通过
        （2）fail:依赖接口无响应
        （3）fail:依赖接口错误xxx
    """

    def __init__(self, depend_interface_list, test_interface_list):
        self.depend_interface_list = depend_interface_list  # 上线的'依赖接口列表'（按照依赖等级顺序排列）
        self.test_interface_list = test_interface_list      # 上线的'测试接口列表'
        self.params_depend_field_list = []                  # '测试接口列表'中的'依赖字段值名列表'（去重）
        self.depend_field_list = []                         # '依赖接口列表'中的'依赖字段值名列表'
        self.depend_interface_result_list = []              # ['fail:依赖接口无响应', 'success:依赖通过']
        self.capture_depend_field_dict = {}                 # {"token":"xxxxx", "image_id":"xxxxx"}

    def get_params_depend_field_list(self):
        """
        获取 '测试接口列表'中的'依赖字段值名列表'（去重）
        ( 接口地址、请求头文件、请求参数 )
        """
        for index, test_interface_dict in enumerate(self.test_interface_list):
            for key, value in test_interface_dict.items():
                if key in ["interface_url", "request_header", "request_params"]:
                    num = value.count('{{')  # 统计参数的依赖字段数量
                    pattern = r'.*{{(.*)}}' * num  # 整理匹配模式（捕获数量）
                    if pattern:  # 若存在 则进行捕获
                        match_obj = re.match(pattern, value)
                        for i in range(num):
                            self.params_depend_field_list.append(match_obj.group(i + 1))
        list(set(self.params_depend_field_list))

    def is_need_depend(self):
        self.get_params_depend_field_list()
        return self.params_depend_field_list != [] or False

    def acquire(self):
        # 1.判断是否存在依赖接口
        if self.depend_interface_list:
            # 2.获取'依赖接口列表'中的'依赖字段值名列表'
            for index, depend_interface_dict in enumerate(self.depend_interface_list):
                self.depend_field_list += depend_interface_dict["depend_field_name_list"]
            # 3.判断 '测试接口列表'中的依赖字段是否都包含在'依赖接口列表'中的依赖字段里面
            no_contain_list = [field for field in self.params_depend_field_list if field not in self.depend_field_list]
            print("self.depend_field_list -> " + str(self.depend_field_list))
            print("self.params_depend_field_list -> " + str(self.params_depend_field_list))
            print("no_contain_list -> " + str(no_contain_list))
            if no_contain_list:
                self.depend_interface_result_list = ["error:依赖字段名配置有误"]
            else:
                # 4.发送'依赖接口'请求 (先按照依赖等级顺序排列),捕获'依赖字段值'
                self.depend_interface_list = sorted(self.depend_interface_list, key=lambda keys: keys['depend_level'])
                for depend_interface_dict in self.depend_interface_list:
                    try:
                        response = VerifyInterface.send_request(request_method=depend_interface_dict["request_method"],
                                                                interface_url=depend_interface_dict["interface_url"],
                                                                request_params=depend_interface_dict["request_params"],
                                                                request_header=depend_interface_dict["request_header"])
                    except Exception as e:
                        log.error(e)
                        self.depend_interface_result_list.append("fail:依赖接口无响应")
                        continue

                    if response.status_code != 200:
                        msg = re.search(r'<title>(.*?)</title>', response.text)
                        self.depend_interface_result_list.append("fail:依赖接口错误,http_code<" + str(response.status_code)
                                                                 + ">,原因解析(" + msg.group(1) + ")")
                    else:
                        # 捕获'依赖字段值'
                        response_dict = json.loads(response.text)
                        for key, value in response_dict.items():
                            if key in self.depend_field_list:
                                self.capture_depend_field_dict[key] = value
                        self.depend_interface_result_list.append("success:依赖通过")

                # 5.判断'依赖字段值'是否全部都获取到
                capture_depend_field_list = self.capture_depend_field_dict.keys()
                no_capture_list = [field for field in self.depend_field_list if field not in capture_depend_field_list]
                if no_capture_list:
                    self.depend_interface_result_list = ["error:依赖字段值没有全部获取到"]
                else:
                    # 替换'测试接口'中的'依赖字段变量'



        else:
            self.depend_interface_result_list = ["error:依赖接口不存在"]

        print("self.depend_interface_result_list -> " + str(self.depend_interface_result_list))
        print("self.capture_depend_field_dict -> " + str(self.capture_depend_field_dict))
        return self.depend_interface_result_list, self.capture_depend_field_dict


class VerifyInterface(object):
    """
    【 验 证 接 口 】
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
      （1）success:通过
      （2）fail:关键字段验证失败
      （3）fail:关键字段验证失败,响应字段列表验证失败
      （4）fail:关键字段验证通过,响应字段列表验证失败
      （5）fail:关键字段验证失败,响应字段列表验证通过
     6.retrun: 待更新字典

       < 验 证 接 口 test_result >
        01.success:测试通过
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
            response = self.send_request(request_method=self.request_method, interface_url=self.interface_url,
                                         request_params=self.request_params, request_header=self.request_header)
        except Exception as e:
            log.error(e)
            self.test_result = "fail:测试接口无响应"
            # 获取 待数据库更新的字典
            self.get_mongo_update_result_dict()
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
        return self.update_result_dict

    # def send_request(self):
    #     if self.request_method == "GET":
    #         response_info = requests.get(url=self.interface_url+self.request_params, headers=self.request_header)
    #     elif self.request_method == "POST":
    #         response_info = requests.post(url=self.interface_url, data=self.request_params, headers=self.request_header)
    #     elif self.request_method == "PUT":
    #         response_info = requests.put(url=self.interface_url, data=self.request_params, headers=self.request_header)
    #     else:
    #         response_info = requests.delete(url=self.interface_url, data=self.request_params, headers=self.request_header)
    #     return response_info

    @staticmethod
    def send_request(request_method, interface_url, request_params, request_header):
        if request_method == "GET":
            response_info = requests.get(url=interface_url+request_params, headers=request_header)
        elif request_method == "POST":
            response_info = requests.post(url=interface_url, data=request_params, headers=request_header)
        elif request_method == "PUT":
            response_info = requests.put(url=interface_url, data=request_params, headers=request_header)
        else:
            response_info = requests.delete(url=interface_url, data=request_params, headers=request_header)
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
    pass
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
