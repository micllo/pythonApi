# -*- coding:utf-8 -*-
import requests
import json
from Common.com_func import is_null, log
import re, copy
from Tools.decorator_tools import retry_request
from Config import pro_config

class VerifyInterface(object):
    """
    【 验 证 接 口 】
     1.转换 参数 格式类型（ 将 mongo 中的 str 类型 转成 需要的类型 ）
        若转换失败，记录'测试结果：test_result'<error:'请求参数'或'请求头文件'格式有误>
        若转换成功，继续
     2.发送请求，验证response响应
      （1）无响应：记录'测试结果：test_result' < fail:测试接口无响应 >
      （2）有相应（ http != 200 ）：记录'测试结果：test_result' < fail:测试接口错误,http_code<500>,原因解析(Internal Server Error)" >
      （3）有响应（ http == 200 ）：继续
     3.记录 '响应信息：response_info' 字段值、获取'实际的响应字段列表、键值字典'
     4.验证'待比较的关键字段名'列表
      （1）验证'待比较的关键字段名'列表是否都存在
      （2）获取'实际的关键字段值'列表
      （3）比较'关键字段值'列表
         记录 '响应字段列表比较结果：result_core_field_value'（ pass、fail、fail:关键字段名不存在）
     5.若'验证模式 = 2'，则还需要验证'待比较的响应字段列表'
         记录 '响应字段列表比较结果：result_field_name_list'（ pass、fail ）
     6.记录 '测试结果：test_result' 字段值
      （1）success:通过
      （2）fail:关键字段验证失败
      （3）fail:关键字段验证失败,响应字段列表验证失败
      （4）fail:关键字段验证通过,响应字段列表验证失败
      （5）fail:关键字段验证失败,响应字段列表验证通过
     7.retrun: 待更新字典

       < 验 证 接 口 test_result >
        01.success:测试通过
        02.fail:关键字段验证失败
        03.fail:关键字段验证失败,响应字段列表验证失败
        04.fail:关键字段验证通过,响应字段列表验证失败
        05.fail:关键字段验证失败,响应字段列表验证通过
        06.fail:测试接口错误,http_code<500>,原因解析(Internal Server Error)
        07.error:'请求参数'或'请求头文件'格式有误
        08.error:上传的文件不存在
        09.error:上传的文件不能为空
        10.error:请求头不能为空
        11.error:请求头中的'Content-Type'类型暂不支持
        12.error:请求头中的'Content-Type'字段不存在
        13.error:上传文件接口的请求头不能包含'Content-Type'


        01.fail:依赖接口无响应
        02.fail:依赖接口错误,http_code<500>,原因解析(Internal Server Error)
        03.error:依赖接口'请求参数'或'请求头文件'格式有误
        04.error:依赖接口上传的文件不存在
        05.error:依赖接口上传的文件不能为空
        06.error:依赖接口请求头不能为空
        07.error:依赖接口请求头中的'Content-Type'类型暂不支持
        08.error:依赖接口请求头中的'Content-Type'字段不存在
        09.error:依赖字段值没有全部获取到(all)
        10.error:依赖字段名配置有遗漏(all)
        11.error:依赖接口不存在(all)

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
        # 验证模式
        self.verify_mode = verify_mode
        # 依赖数据
        self.depend_interface_list = depend_interface_list
        self.depend_field_name_list = depend_field_name_list
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

        # 1.转换 参数 格式类型
        error_msg, file, self.request_params, self.request_header = \
            self.transform_params_format(request_params=self.request_params, request_header=self.request_header,
                                         request_method=self.request_method)
        if error_msg:
            self.test_result = "error:" + error_msg
        else:
            # 2.发送请求，验证response响应
            response = self.send_request(request_method=self.request_method, interface_url=self.host+self.interface_url,
                                         request_params=self.request_params, request_header=self.request_header, file=file)
            if response == 31500:
                self.test_result = "fail:测试接口无响应"
            elif response.status_code != 200:
                msg = re.search(r'<title>(.*?)</title>', response.text)
                self.test_result = "fail:测试接口错误,http_code<" + str(response.status_code) + ">,原因解析(" + msg.group(1) + ")"
            else:
                # 4.记录'响应信息：response_info'字段值、获取'实际的响应字段列表、键值字典'
                self.response_info = response.text
                self.response_dict = json.loads(self.response_info)
                self.get_response_field_list_and_dict()

                # 5.验证'待比较的关键字段'列表
                self.verify_core_field_list()

                # 6.若'验证模式 = 2'，则验证'待比较的响应字段列表'
                self.verify_mode == 2 and self.verify_response_field_name_list()

                # 7.记录 '测试结果：test_result' 字段值
                self.get_test_result()

        # 获取 待数据库更新的字典
        self.get_mongo_update_result_dict()
        return self.update_result_dict

    @staticmethod
    def transform_params_format(request_params, request_header, request_method):
        """
        转换 参数 格式类型（ 将 mongo 中的 str 类型 转成 需要的类型 ）
        1.'请求头'格式转换：
            若非空，则 str -> dict
        2.'GET'请求的参数转换方式：
             转成字典类型 ：?key=value&key=value' -> {"key": "value"}
        3.'POST,PUT,DELETE'请求的参数转换方式：
            先 转成字典类型（方便判断）
        （1）判断当前是否为上传文件的请求 < 是否存在'file'字段 >
            1）若是：
                将该字段的键值对提取出来存放入 file字典中
                请求头中不能包含 Content-Type 字段
            2）若不是
                判断'请求头'中的'Content-Type'
                  请求头是否存在
                  请求头中的'Content-Type'是否存在
                  请求头中的'Content-Type'是否为支持的类型
        （2）判断 入参格式
            1）若 Content-Type = application/json，则请求参数转换成 字符串
            2）若 Content-Type = application/x-www-form-urlencoded，则请求参数转换成 字典


         < files 字典的三种情况 >
          files = {}
          files = {"file": ""}
          files = {'file': (file_name, open(file_path, 'rb'))}

        < 当前仅支持 请求头的 Content-Type 的类型 >
        （1）application/json
        （2）application/x-www-form-urlencoded

        """
        error_msg = None
        files = {}
        try:
            # 1.'请求头'格式转换：若非空，则 str -> dict
            request_header = request_header and eval(request_header)
            if request_method == "GET":
                if request_params:  # '?key=value&key=value' -> {"key": "value"}
                    params = copy.copy(request_params)
                    params = params[1:]
                    params = params.split("&")
                    request_params = {}
                    for each in params:
                        each_list = each.split("=")
                        request_params[each_list[0]] = each_list[1]
                else:
                    request_params = {}
            else:  # "POST", "PUT", "DELETE"
                # 请求参数 先统一改成 字典 格式
                request_params = eval(request_params)
                # 判断当前是否为上传文件的请求
                if "file" in request_params.keys():
                    if "Content-Type" in request_header.keys():
                        error_msg = "上传文件接口的请求头不能包含'Content-Type'"
                    else:
                        files["file"] = request_params.get("file")
                        del request_params["file"]
                        if files["file"]:
                            file_path = files["file"]
                            file_name = file_path.split("/")[-1]
                            try:
                                # 提取 file 字典
                                files["file"] = (file_name, open(file_path, 'rb'))
                            except Exception as e:
                                log.error(e)
                                error_msg = "上传的文件不存在"
                        else:
                            error_msg = "上传的文件不能为空"
                else:
                    if not request_header:
                        error_msg = "请求头不能为空"
                    elif not request_header.get("Content-Type", ""):
                        error_msg = "请求头中的'Content-Type'字段不存在"
                    elif request_header["Content-Type"] not in pro_config.get_content_type_list():
                        error_msg = "请求头中的'Content-Type'类型暂不支持"
                    # 判断 入参格式
                    request_params = "json" in request_header["Content-Type"] and json.dumps(request_params) or request_params

        except Exception as e:
            log.error(e)  # "invalid syntax"
            error_msg = "'请求参数'或'请求头文件'格式有误"
        return error_msg, files, request_params, request_header

    # try_func = retry_request(try_limit=3,interval_time=1,send_dd=True)
    # send_request = try_func(send_request)
    @staticmethod
    @retry_request(try_limit=3, interval_time=1, send_dd=True)
    def send_request(request_method, interface_url, request_params, request_header, file):
        """
        【 发 送 请 求 】
        :param request_method:
        :param interface_url:
        :param request_params:
        :param request_header:
        :param file:  上传文件接口
        :return:

            【 注 意 事 项 】
            1."POST、PUT、DELETE"请求，必须要包含有 'Content-Type' 字段
            2."Content-Type"：目前支持的类型
            （1）application/json
            （2）application/x-www-form-urlencoded

            【 备 注 】
            1.请求默认超时时间，设置 5 秒
            2.失败重试次数，设置 3 次 （每次间隔 1 秒）
            3.一个请求最长用时：5 * 3 + 2 = 17 秒
        """
        if request_method == "GET":
            response_info = requests.get(url=interface_url, params=request_params, headers=request_header, timeout=5)
        elif request_method == "POST":
            if file:
                response_info = requests.post(url=interface_url, data=request_params, files=file, headers=request_header, timeout=5)
            else:
                response_info = requests.post(url=interface_url, data=request_params, headers=request_header, timeout=5)
        elif request_method == "PUT":
            response_info = requests.put(url=interface_url, data=request_params, headers=request_header, timeout=5)
        else:  # DELETE
            response_info = requests.delete(url=interface_url, data=request_params, headers=request_header, timeout=5)
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
        1.success:测试通过
        2.fail:关键字段验证失败
        3.fail:关键字段验证失败,响应字段列表验证失败
        4.fail:关键字段验证通过,响应字段列表验证失败
        5.fail:关键字段验证失败,响应字段列表验证通过
        :return:
        """
        if self.verify_mode == 1:
            self.test_result = self.result_core_field_value == "pass" and "success:测试通过" or "fail:关键字段验证失败"
        else:
            if self.result_core_field_value != "pass" and self.result_field_name_list != "pass":
                self.test_result = "fail:关键字段验证失败,响应字段列表验证失败"
            elif self.result_core_field_value == "pass" and self.result_field_name_list != "pass":
                self.test_result = "fail:关键字段验证通过,响应字段列表验证失败"
            elif self.result_core_field_value != "pass" and self.result_field_name_list == "pass":
                self.test_result = "fail:关键字段验证失败,响应字段列表验证通过"
            else:
                self.test_result = "success:测试通过"

    def get_mongo_update_result_dict(self):
        """
        【 获取 待数据库更新的字典 】
        """
        self.update_result_dict = {"response_info": self.response_info,
                                   "actual_core_field_value_list": self.actual_core_field_value_list,
                                   "actual_field_name_list": self.actual_field_name_list,
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
