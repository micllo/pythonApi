# -*- coding:utf-8 -*-
import json
from Tools.mongodb import MongodbUtils
from Env import env_config as cfg
from Tools.date_helper import get_current_iso_date
from Common.com_func import is_null, mongo_exception_send_DD
import re
from Common.verify_interface import VerifyInterface


class AcquireDependField(object):
    """
     【 获 取 依 赖 字 段 值 】
     0.获取'测试接口列表'中的'参数依赖字段名列表'（去重）( 接口地址、请求头文件、请求参数 )
       < 根据 '参数依赖字段名列表' 判断是否需要 执行依赖接口 >
     1.<判断> 是否存在依赖接口
      （1）若不存在，则'整体记录' < error:依赖接口不存在 >
      （2）若存在，则 继续
     2.获取'依赖接口列表'中的'依赖字段名列表'，并清空相关结果记录
     3.<判断> '测试接口列表'中的依赖字段是否都包含在'依赖接口列表'中的依赖字段里面
      （1）若存在不包含的情况，则'整体记录' < error:依赖字段名配置有遗漏(all) >
         （ 由于没有进行请求,所以需要给每个用例的"response_info"设置为空 ）
      （2）若全包含，则 继续
     4.'依赖接口列表'按照依赖等级排序
     5.循环发送'依赖接口列表'中的请求
      （1）替换'依赖接口'中的'依赖变量'（依赖接口也存在依赖关系）
      （2）转换 '请求参数'或'请求头文件' 格式类型 <判断>（ 将 mongo 中的 str 类型 转成 需要的类型 ）
            若转换失败，'分开记录'< error:依赖接口'请求参数'或'请求头文件'格式有误 >
            若转换成功 <判断> 响应码
            1）无响应：'分开记录' < fail:依赖接口无响应 >
            2）有相应（ http != 200 ）：'分开记录'< fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)" >
            3）有响应（ http == 200 ）：'分开记录'< success:依赖通过 >、捕获'依赖字段值'、获取'依赖接口'中的'依赖字段值列表'并判断依赖字段是否获取到
     6.获取'依赖接口'执行失败的结果列表 < 判断 >
      （1）若存在'fail'，则不做处理，保持原有结果记录
      （2）若全部是'success'，则 < 判断 > '依赖字段值'是否全部都获取到
           1）是，则 替换'测试接口列表'中的'依赖字段变量'（依赖字段捕获成功）
           2）否，则 '整体记录' < error:依赖字段值没有全部获取到 >
     7.若存在(all)的失败用例,则需要给每个用例的"test_result"设置为该(all)结果
     8.更新'依赖接口列表'、'测试接口列表'结果
        < 判断 > 测试接口列表
       （1）若 '依赖接口'测试结果 全部是'success' 则 不更新 '测试接口列表' 结果
       （2）若 '依赖接口'测试结果 存在'error'或'fail' 则 所有的 '测试接口列表' 结果 都更新（选择第一个结果进行保存）
               并清除相关'测试记录'内容，同时改变'接口验证标记'（表示：不需要在验证测试接口）
     RETURN：test_interface_list

       < 依 赖 接 口 test_result >
        01.success:依赖通过
        02.fail:依赖接口无响应
        03.fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)
        04.error:依赖字段没有获取到
        05.error:依赖字段名配置有遗漏(all)
        06.error:依赖字段值没有全部获取到(all)
        07.error:依赖接口'请求参数'或'请求头文件'格式有误

        [ 备 注 ]
        1.'error:依赖接口不存在(all)'不记录在'依赖接口 test_result'中，而是记录在'测试接口 test_result'中
        2.依赖接口列表 整体记录 的 'test_result'
        （1）error:依赖接口不存在(all)
        （2）error:依赖字段名配置有遗漏(all)
        （3）error:依赖字段值没有全部获取到(all)
        3.依赖接口列表 分开记录 的 'test_result':
        （1）success:依赖通过
        （2）fail:依赖接口无响应
        （3）fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)
        （4）error:依赖接口'请求参数'或'请求头文件'格式有误
        （5）error:依赖字段没有获取到

        举例：
        1.整体记录：["error:依赖字段名配置有遗漏(all)", "error:依赖字段名配置有遗漏(all)"]
        2.分开记录：["success:依赖通过", "fail:依赖接口错误xxx"]
    """

    def __init__(self, pro_name, host, depend_interface_list, test_interface_list):
        self.pro_name = pro_name
        self.host = host
        self.response_info_list = []
        self.depend_interface_list = depend_interface_list  # 上线的'依赖接口列表'（按照依赖等级顺序排列）
        self.test_interface_list = test_interface_list      # 上线的'测试接口列表'
        self.params_depend_field_list = []                  # '测试接口列表'中的'依赖字段名列表'（测试接口中捕获的依赖字段）
        self.depend_field_list = []                         # '依赖接口列表'中的'依赖字段名列表'（依赖接口中设置的依赖字段）
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
            # 替换 接口中的'依赖字段'变量
            if key in ["interface_url", "request_header", "request_params"]:
                for field in self.capture_depend_field_dict.keys():
                    interface_dict[key] = interface_dict[key].replace("{{" + field + "}}", self.capture_depend_field_dict[field])

    def get_depend_field_value(self, depend_interface_dict):
        """
        获取 '依赖接口' 中的 '依赖字段值列表'
        :param depend_interface_dict:
        :return:
          判断 字段值列表数量 是否与 字段名列表数量 一致
        """
        depend_interface_dict["depend_field_value_list"] = [value for key, value in self.capture_depend_field_dict.items()
                                                            if key in depend_interface_dict["depend_field_name_list"]]
        return len(depend_interface_dict["depend_field_value_list"]) == len(depend_interface_dict["depend_field_name_list"])

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
        if is_null(self.depend_interface_list):
            self.depend_interface_result_list = ["error:依赖接口不存在(all)"]
        else:
            # 2.获取'依赖接口列表'中的'依赖字段名列表'（去重、排序），并清空相关结果记录
            for index, depend_interface_dict in enumerate(self.depend_interface_list):
                self.depend_field_list += depend_interface_dict["depend_field_name_list"]
                depend_interface_dict["test_result"] = ""
                depend_interface_dict["response_info"] = ""
                depend_interface_dict["depend_field_value_list"] = ""
            self.depend_field_list = list(set(self.depend_field_list))
            self.depend_field_list.sort()

            # 3.判断 '测试接口列表'中的依赖字段是否都包含在'依赖接口列表'中的依赖字段里面
            no_contain_list = [field for field in self.params_depend_field_list if field not in self.depend_field_list]
            if no_contain_list:
                self.response_info_list.append("")
                # 由于没有进行请求,所以需要给每个用例的"response_info"设置为空
                # 将需要整体记录的'response_info'，按照依赖列表个数赋值给'response_info_list'
                self.response_info_list = self.response_info_list * len(self.depend_interface_list)
                self.depend_interface_result_list = ["error:depend_field_list(all)"]
            else:
                # 4.'依赖接口列表'按照依赖等级排序
                self.depend_interface_list = sorted(self.depend_interface_list, key=lambda keys: keys['depend_level'])

                # 5.循环发送'依赖接口列表'中的请求
                for depend_interface_dict in self.depend_interface_list:

                    # 替换'依赖接口'中的'依赖变量'（依赖接口也存在依赖关系）
                    self.replace_params(depend_interface_dict)

                    # 转换 '请求参数'或'请求头文件' 格式类型（ 将 mongo 中的 str 类型 转成 需要的类型 ）
                    transform_fail, depend_interface_dict["request_params"], depend_interface_dict["request_header"] = \
                        VerifyInterface.transform_params_format(request_params=depend_interface_dict["request_params"],
                                                                request_header=depend_interface_dict["request_header"])
                    if transform_fail:
                        self.response_info_list.append("")
                        self.depend_interface_result_list.append("error:依赖接口'请求参数'或'请求头文件'格式有误")
                    else:
                        response = VerifyInterface.send_request(request_method=depend_interface_dict["request_method"],
                                                                interface_url=self.host + depend_interface_dict["interface_url"],
                                                                request_params=depend_interface_dict["request_params"],
                                                                request_header=depend_interface_dict["request_header"])
                        if response == 31500:
                            self.response_info_list.append("")
                            self.depend_interface_result_list.append("fail:依赖接口无响应")
                        elif response.status_code != 200:
                            self.response_info_list.append(response.text)
                            msg = re.search(r'<title>(.*?)</title>', response.text)
                            self.depend_interface_result_list.append(
                                "fail:依赖接口错误,http_code<" + str(response.status_code)
                                + ">,原因解析(" + msg.group(1) + ")")
                        else:
                            self.response_info_list.append(response.text)
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

                            # 获取'依赖接口'中的'依赖字段值列表' 并判断依赖字段是否获取到
                            is_capture = self.get_depend_field_value(depend_interface_dict)
                            if is_capture:
                                self.depend_interface_result_list.append("success:依赖通过")
                            else:
                                self.depend_interface_result_list.append("error:依赖字段没有获取到")

                # 6.获取'依赖接口'执行失败的结果列表 < 判断 >
                fail_result_list = [result for result in self.depend_interface_result_list if "success" not in result]
                # 若全部是'success'，则 < 判断 > '依赖字段值'是否全部都获取到
                if not fail_result_list:
                    capture_depend_field_list = self.capture_depend_field_dict.keys()
                    no_capture_list = [field for field in self.params_depend_field_list if field not in capture_depend_field_list]
                    if no_capture_list:
                        self.depend_interface_result_list = ["error:依赖字段值没有全部获取到(all)"]
                    else:
                        # 替换'测试接口列表'中的'依赖字段变量'（依赖字段捕获成功）
                        for test_interface_dict in self.test_interface_list:
                            self.replace_params(test_interface_dict)

            # 7.若存在(all)的失败用例,则需要给每个用例的"test_result"设置为该(all)结果
            #   将需要整体记录的'test_result'，按照依赖列表个数赋值给'depend_interface_result_list'
            error_result = [result for result in self.depend_interface_result_list if "(all)" in result]
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
        （1）test_result：依赖测试结果
        （2）depend_field_value_list：依赖字段值列表
        :return:
        """
        with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=self.pro_name + "_case") as pro_db:
            try:
                for index, depend_interface_dict in enumerate(self.depend_interface_list):
                    query_dict = {"_id": depend_interface_dict["_id"]}
                    update_dict = {"update_time": update_time, "test_result": self.depend_interface_result_list[index],
                                   "depend_field_value_list": depend_interface_dict["depend_field_value_list"],
                                   "response_info": self.response_info_list[index]}
                    pro_db.update(query_dict, {"$set": update_dict})
            except Exception as e:
                mongo_exception_send_DD(e=e, msg="更新'" + self.pro_name + "'项目依赖接口结果")
                return "mongo error"

    def update_test_interface_list_result(self, update_time):
        """
        更新'测试接口列表'结果
        （1）若 '依赖接口'测试结果 全部是'success' 则 不更新 '测试接口列表' 结果
        （2）若 '依赖接口'测试结果 存在'error'或'fail' 则 所有的 '测试接口列表' 结果 都更新（选择第一个结果进行保存）
                并清除相关'测试记录'内容，同时改变'接口验证标记'（表示：不需要在验证测试接口）
        :return:
        """
        wang_result = [result for result in self.depend_interface_result_list if "error" in result or "fail" in result]
        if wang_result:
            self.verify_flag = False
            with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=self.pro_name + "_case") as pro_db:
                try:
                    for index, test_interface_dict in enumerate(self.test_interface_list):
                        query_dict = {"_id": test_interface_dict["_id"]}
                        update_dict = {"update_time": update_time, "test_result": wang_result[0], "response_info": "",
                                       "actual_core_field_value_list": [], "actual_field_name_list": [],
                                       "result_core_field_value": "", "result_field_name_list": ""}
                        pro_db.update(query_dict, {"$set": update_dict})
                except Exception as e:
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
        print("依赖接口执行结果列表 -> " + str(self.depend_interface_result_list))
        print("\n===========================[ depend_interface_list ]==================================\n")
        for index, depend_interface_dict in enumerate(self.depend_interface_list):
            print("depend_level  " + str(depend_interface_dict["depend_level"]))
            print("interface_name  " + depend_interface_dict["interface_name"])
            print("interface_url  " + depend_interface_dict["interface_url"])
            print("request_header  " + str(depend_interface_dict["request_header"]))
            print("request_params  " + str(depend_interface_dict["request_params"]))
            print("-----")
        print("\n===========================[ test_interface_list ]==================================\n")
        for index, test_interface_dict in enumerate(self.test_interface_list):
            print("interface_name  " + test_interface_dict["interface_name"])
            print("interface_url  " + test_interface_dict["interface_url"])
            print("request_header  " + str(test_interface_dict["request_header"]))
            print("request_params  " + str(test_interface_dict["request_params"]))
            print("-----")
