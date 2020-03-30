# -*- coding:utf-8 -*-
import requests
import json


class RequestInterface(object):

    def __init__(self, interface_name, interface_url, request_method, request_header, request_params):
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

    def send_request(self):
        if self.request_method == "GET":
            response = requests.get(url=self.interface_url+self.request_params, headers=self.request_header)
        elif self.request_method == "POST":
            response = requests.post(url=self.interface_url, data=self.request_params, headers=self.request_header)
        elif self.request_method == "PUT":
            response = requests.put(url=self.interface_url, data=self.request_params, headers=self.request_header)
        else:
            response = requests.delete(url=self.interface_url, data=self.request_params, headers=self.request_header)
        return response


if __name__ == "__main__":

    # http://127.0.0.1:7060/api_local/test/test_get_request?test_str=接口自动化测试&test_int=5&test_bool=True
    # http://127.0.0.1:7060/api_local/test/test_post_request   {"test_str":"post测试","test_int":5,"test_bool":"true"}

    # interface_name = "测试带参数的get请求"
    # interface_url = "http://127.0.0.1:7060/api_local/test/test_get_request"
    # request_method = "GET"
    # request_header = ""
    # request_params = "?test_str=接口自动化测试&test_int=5&test_bool=True"

    interface_name = "测试post请求"
    interface_url = "http://127.0.0.1:7060/api_local/test/test_post_request"
    request_method = "POST"
    request_header = "{\"Content-Type\": \"application/json\"}"
    request_params = "{\"test_str\":\"post测试\",\"test_int\":5,\"test_bool\":\"true\"}"

    ri = RequestInterface(interface_name=interface_name, interface_url=interface_url, request_method=request_method,
                          request_header=request_header, request_params=request_params)
    respone = ri.send_request()
    print(respone)
    print(respone.status_code)
    print(respone.text)
