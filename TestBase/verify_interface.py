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
     1.<判断> 是否存在依赖接口
      （1）若不存在，则'整体记录' < error:依赖接口不存在 >
      （2）若存在，则 继续
     2.获取'依赖接口列表'中的'依赖字段值名列表'
     3.<判断> '测试接口列表'中的依赖字段是否都包含在'依赖接口列表'中的依赖字段里面
      （1）若存在不包含的情况，则'整体记录' < error:依赖字段名配置有误 >
      （2）若全包含，则 继续
     4.'依赖接口列表'按照依赖等级排序
     5.循环发送'依赖接口列表'中的请求
      （1）替换'依赖接口'中的'依赖变量'
      （2）<判断> 响应码
           1）无响应：'分开记录' < fail:依赖接口无响应 >
           2）有相应（ http != 200 ）：'分开记录'< fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)" >
           3）有响应（ http == 200 ）：'分开记录'< success:依赖通过 >、捕获'依赖字段值'
     6.获取'依赖接口'执行失败的结果列表 < 判断 >
      （1）若存在'fail'，则不做处理，保持原有结果记录
      （2）若全部是'success'，则 < 判断 > '依赖字段值'是否全部都获取到
           1）是，则 替换'测试接口列表'中的'依赖字段变量'
           2）否，则 '整体记录' < error:依赖字段值没有全部获取到 >
     7.将需要整体记录的'test_result'，按照依赖接口个数赋值给'depend_interface_result_list'
     8.更新'依赖接口列表'、'测试接口列表'结果
        < 判断 > '测试接口列表'
       （1）若 全部是'success' 则 不更新
       （2）若 存在'error'或'fail' 则 所有的测试接口结果 都更新（选择第一个结果进行保存），
            同时改变'接口验证标记'（表示：不需要在验证测试接口）
     RETURN：test_interface_list

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
        （3）fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)

        举例：
        1.整体记录：["error:依赖接口不存在", "error:依赖接口不存在"]
        2.分开记录：["success:依赖通过", "fail:依赖接口错误xxx"]
    """

    def __init__(self, pro_name, host, depend_interface_list, test_interface_list):
        self.pro_name = pro_name
        self.host = host
        self.depend_interface_list = depend_interface_list  # 上线的'依赖接口列表'（按照依赖等级顺序排列）
        self.test_interface_list = test_interface_list      # 上线的'测试接口列表'
        self.params_depend_field_list = []                  # '测试接口列表'中的'依赖字段值名列表'（测试接口中捕获的依赖字段）
        self.depend_field_list = []                         # '依赖接口列表'中的'依赖字段值名列表'（依赖接口中设置的依赖字段）
        self.depend_interface_result_list = []              # '依赖接口列表'执行结果 ['fail:依赖接口无响应', 'success:依赖通过']
        self.capture_depend_field_dict = {}                 # 捕获的依赖字段键值对 {"token":"xxxxx", "image_id":"xxxxx"}
        self.verify_flag = True                             # 接口测试标记 True：需要验证、False：不需要验证

    def get_params_depend_field_list(self):
        """
        获取 '测试接口列表'中的'依赖字段名列表'（去重、排序）
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
        self.params_depend_field_list = list(set(self.params_depend_field_list))
        self.params_depend_field_list.sort()

    def replace_params(self, interface_dict):
        """
        替换 '接口字典'中的'依赖字段变量' ( 接口地址、请求头文件、请求参数 )
        :param interface_dict  测试接口字典、依赖接口字典
        :return:
        """
        for key, value in interface_dict.items():
            if key in ["interface_url", "request_header", "request_params"]:
                for field in self.capture_depend_field_dict.keys():
                    interface_dict[key] = interface_dict[key].replace("{{" + field + "}}", self.capture_depend_field_dict[field])

    def is_need_depend(self):
        """
        判断 是否需要依赖
        :return:
        """
        self.get_params_depend_field_list()
        return self.params_depend_field_list != [] or False

    def acquire(self):
        """
        获取 依赖字段值
        :return:
        """
        # 1.判断是否存在依赖接口
        if self.depend_interface_list:

            # 2.获取'依赖接口列表'中的'依赖字段值名列表'（去重、排序）
            for index, depend_interface_dict in enumerate(self.depend_interface_list):
                self.depend_field_list += depend_interface_dict["depend_field_name_list"]
            self.depend_field_list = list(set(self.depend_field_list))
            self.depend_field_list.sort()

            # 3.判断 '测试接口列表'中的依赖字段是否都包含在'依赖接口列表'中的依赖字段里面
            no_contain_list = [field for field in self.params_depend_field_list if field not in self.depend_field_list]
            if no_contain_list:
                self.depend_interface_result_list = ["error:依赖字段名配置有误"]
            else:
                # 4.'依赖接口列表'按照依赖等级排序
                self.depend_interface_list = sorted(self.depend_interface_list, key=lambda keys: keys['depend_level'])

                # 5.循环发送'依赖接口列表'中的请求
                for depend_interface_dict in self.depend_interface_list:
                    self.replace_params(depend_interface_dict)  # 替换'依赖接口'中的'依赖变量'
                    try:
                        response = VerifyInterface.send_request(request_method=depend_interface_dict["request_method"],
                                                                interface_url=self.host+depend_interface_dict["interface_url"],
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
                        # 递归捕获'依赖字段值' ( 暂时递归三层进行捕获 )
                        response_dict = json.loads(response.text)
                        for key, value in response_dict.items():
                            if key in self.depend_field_list:
                                self.capture_depend_field_dict[key] = value
                            if isinstance(value, dict):  # 若第一层的value是字典类型，则继续遍历捕获
                                for key_2, value_2 in value.items():
                                    if key_2 in self.depend_field_list:
                                        self.capture_depend_field_dict[key_2] = value_2
                                    if isinstance(value_2, dict):  # 若第二层的value_2是字典类型，则继续遍历捕获
                                        for key_3, value_3 in value.items():
                                            if key_3 in self.depend_field_list:
                                                self.capture_depend_field_dict[key_3] = value_3
                        self.depend_interface_result_list.append("success:依赖通过")

                # 6.获取'依赖接口'执行失败的结果列表 < 判断 >
                fail_result_list = [result for result in self.depend_interface_result_list if "success" not in result]
                # 若全部是'success'，则 < 判断 > '依赖字段值'是否全部都获取到
                if not fail_result_list:
                    capture_depend_field_list = self.capture_depend_field_dict.keys()
                    no_capture_list = [field for field in self.params_depend_field_list if field not in capture_depend_field_list]
                    if no_capture_list:
                        self.depend_interface_result_list = ["error:依赖字段值没有全部获取到"]
                    else:
                        # 替换'测试接口列表'中的'依赖字段变量'
                        for test_interface_dict in self.test_interface_list:
                            self.replace_params(test_interface_dict)
        else:
            self.depend_interface_result_list = ["error:依赖接口不存在"]

        # 7.将需要整体记录的'test_result'，按照依赖列表个数赋值给'depend_interface_result_list'
        error_result = [result for result in self.depend_interface_result_list if "error" in result]
        if error_result:
            self.depend_interface_result_list = self.depend_interface_result_list * len(self.depend_interface_list)

        # 8.更新'依赖接口列表'、'测试接口列表'结果
        update_time = get_current_iso_date()
        self.update_depend_interface_list_result(update_time)
        self.update_test_interface_list_result(update_time)

        # 显示相关变量字段（调试使用）
        self.debug_variable_field()
        return self.test_interface_list

    def update_depend_interface_list_result(self, update_time):
        """
        更新'依赖接口列表'结果
        :return:
        """
        with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=self.pro_name) as pro_db:
            try:
                for index, depend_interface_dict in enumerate(self.depend_interface_list):
                    query_dict = {"_id": depend_interface_dict["_id"]}
                    update_dict = {"update_time": update_time, "test_result": self.depend_interface_result_list[index]}
                    pro_db.update(query_dict, {"$set": update_dict})
            except Exception as e:
                from Common.test_func import mongo_exception_send_DD
                mongo_exception_send_DD(e=e, msg="更新'" + self.pro_name + "'项目依赖接口结果")
                return "mongo error"

    def update_test_interface_list_result(self, update_time):
        """
        更新'测试接口列表'结果
        （1）若 全部是'success' 则 不更新
        （2）若 存在'error'或'fail' 则 所有的测试接口结果 都更新（选择第一个结果进行保存），
            同时改变'接口验证标记'（表示：不需要在验证测试接口）
        :return:
        """
        wang_result = [result for result in self.depend_interface_result_list if "error" in result or "fail" in result]
        if wang_result:
            self.verify_flag = False
            with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=self.pro_name) as pro_db:
                try:
                    for index, test_interface_dict in enumerate(self.test_interface_list):
                        query_dict = {"_id": test_interface_dict["_id"]}
                        update_dict = {"update_time": update_time, "test_result": wang_result[0]}
                        pro_db.update(query_dict, {"$set": update_dict})
                except Exception as e:
                    from Common.test_func import mongo_exception_send_DD
                    mongo_exception_send_DD(e=e, msg="更新'" + self.pro_name + "'项目测试接口结果")
                    return "mongo error"

    def debug_variable_field(self):
        """
        显 示 相 关 变 量 字 段
        :return:
        """
        print("依赖接口中设置的依赖字段 -> " + str(self.depend_field_list))
        print("测试接口中捕获的依赖字段 -> " + str(self.params_depend_field_list))
        print("捕获的依赖字段键值对 -> " + str(self.capture_depend_field_dict))
        print("依赖接口执行结果 -> " + str(self.depend_interface_result_list))
        print("\n===========================[ depend_interface_list ]==================================\n")
        for index, depend_interface_dict in enumerate(self.depend_interface_list):
            print("depend_level  " + str(depend_interface_dict["depend_level"]))
            print("interface_name  " + depend_interface_dict["interface_name"])
            print("interface_url  " + depend_interface_dict["interface_url"])
            print("request_header  " + depend_interface_dict["request_header"])
            print("request_params  " + depend_interface_dict["request_params"])
            print("-----")
        print("\n===========================[ test_interface_list ]==================================\n")
        for index, test_interface_dict in enumerate(self.test_interface_list):
            print("interface_name  " + test_interface_dict["interface_name"])
            print("interface_url  " + test_interface_dict["interface_url"])
            print("request_header  " + test_interface_dict["request_header"])
            print("request_params  " + test_interface_dict["request_params"])
            print("-----")


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
        09.error:依赖字段值没有全部获取到
        10.error:依赖字段名配置有误
        11.error:依赖接口不存在
    """

    def __init__(self, host, interface_name, interface_url, request_method, request_header, request_params,
                 verify_mode, compare_core_field_name_list, expect_core_field_value_list, expect_field_name_list,
                 depend_interface_list, depend_field_name_list):
        # 请求相关
        self.host = host
        self.interface_name = interface_name
        self.interface_url = interface_url
        self.request_method = request_method
        self.request_header = request_header
        self.request_params = request_params
        # if request_header:
        #     self.request_header = eval(request_header)  # string -> dict
        # else:  # ""
        #     self.request_header = request_header
        # if request_params and request_params.startswith("{"):
        #     self.request_params = json.dumps(eval(request_params))  # string -> dict -> json
        # else:  # "" 或 '?xx=xx'
        #     self.request_params = request_params

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
            response = self.send_request(request_method=self.request_method, interface_url=self.host+self.interface_url,
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

    @staticmethod
    def send_request(request_method, interface_url, request_params, request_header):

        # 类 型 转 换
        # 若 request_header = ""，则保持不变，否则 string -> dict
        request_header = request_header and eval(request_header)

        # 若 request_params 是以"{"开头的，则 string -> dict -> json，否则 保持不变（ "" 或 '?xx=xx' ）
        if request_params and request_params.startswith("{"):
            request_params = json.dumps(eval(request_params))  # string -> dict -> json
        else:  # "" 或 '?xx=xx'
            request_params = request_params

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
        self.recur_caputure_params(self.response_info)
        self.actual_field_name_list = list(set(self.actual_field_name_list))

    def recur_caputure_params(self, response_info):
        """
        递归 捕获 参数
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
            self.recur_caputure_params(response_info_dict)
        elif isinstance(response_info, dict):
            for field, value in response_info.items():
                self.actual_field_name_list.append(field)
                if isinstance(value, list):
                    for field in value:
                        self.recur_caputure_params(field)
                elif isinstance(value, dict):
                    self.recur_caputure_params(value)
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
