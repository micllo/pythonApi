# -*- coding:utf-8 -*-


class RequestInterface(object):

     def __init__(self, interface_name, interface_url, request_method, request_header, request_params):
        self.interface_name = interface_name
        self.interface_url = interface_url
        self.request_method = request_method
        self.request_header = request_header
        self.request_params = request_params

     # def transfer_params_format(self):
     #    if self.request_params:



