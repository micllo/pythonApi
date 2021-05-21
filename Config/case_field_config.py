
def get_case_field_name():
    """
    获取用例字段名（用于Excel头部的显示）
    :return:
     【 注 意 事 项 】
      列表顺序 必须和 数据库中的顺序 保持一致
    """
    field_name_dict = {}
    field_name_dict["interface_name"] = "接口名称"
    field_name_dict["interface_url"] = "接口地址"
    field_name_dict["request_method"] = "请求方式"
    field_name_dict["request_header"] = "请求头文件"
    field_name_dict["request_params"] = "请求参数"
    field_name_dict["verify_mode"] = "验证模式"

    field_name_dict["compare_core_field_name_list"] = "待比较关键字段名列表"
    field_name_dict["expect_core_field_value_list"] = "期望的关键字段值列表"
    field_name_dict["expect_field_name_list"] = "期望的响应字段列表"

    field_name_dict["is_depend"] = "是否为依赖接口"
    field_name_dict["depend_field_name_list"] = "依赖字段名列表"
    field_name_dict["depend_level"] = "依赖等级"

    field_name_dict["case_status"] = "用例状态"

    field_name_dict["response_info"] = "响应信息"
    field_name_dict["depend_field_value_list"] = "依赖字段值列表"

    field_name_dict["actual_core_field_value_list"] = "实际的关键字段值列表"
    field_name_dict["actual_field_name_list"] = "实际的响应字段列表"

    field_name_dict["result_core_field_value"] = "关键字段值比较结果"
    field_name_dict["result_field_name_list"] = "响应字段列表比较结果"

    field_name_dict["test_result"] = "测试结果"
    field_name_dict["run_status"] = "运行状态"
    field_name_dict["update_time"] = "上次执行时间"
    field_name_dict["create_time"] = "创建时间"

    return field_name_dict


def get_case_special_field_list():
    """
    【 获 取 excel 用 例 的 指 定 字 段 名 称 】
    01.接口名称：interface_name（ 必填 ）
    02.接口地址：interface_url （ 必填 ）
    03.请求方式：request_method（ 必填 ）
    04.请求头文件：request_header
    05.请求参数：request_params
    06.验证模式：verify_mode    （ 测试必填 ） < (Excel)float  -> (Mongo)int >

    07.待比较关键字段名列表：compare_core_field_name_list （ 测试必填 ）< (Excel)string -> (Mongo)list >（以","分割）
    08.期望的关键字段值列表：expect_core_field_value_list （ 测试必填 ）< (Excel)string -> (Mongo)list >（以","分割）
    09.期望的响应字段列表：expect_field_name_list                   < (Excel)string -> (Mongo)list >（以","分割）

    10.是否为依赖接口：is_depend              （ 必填 ）     < (Excel)int|string -> (Mongo)bool >
    11.依赖等级：depend_level                （ 依赖必填 ）  < (Excel)float  -> (Mongo)int >
    12.依赖字段名列表：depend_field_name_list （ 依赖必填 ）  < (Excel)string -> (Mongo)list >（以","分割）
    13.用例状态：case_status  （ 默认：FALSE ）             < (Excel)int|string -> (Mongo)bool >

    < 以下字段不显示在导入Excel中>
    14.响应信息：response_info
    15.依赖字段值列表：depend_field_value_list             < (Mongo)list -> (Excel)string >
    16.实际的关键字段值列表：actual_core_field_value_list   < (Mongo)list -> (Excel)string >
    17.实际的响应字段列表：actual_field_name_list           < (Mongo)list -> (Excel)string >
    18.关键字段值比较结果：result_core_field_value
    19.响应字段列表比较结果：result_field_name_list
    20.测试结果：test_result
    21.运行状态：run_status    < (Mongo)bool -> (Excel)string >
    22.创建时间：create_time   < (Mongo)ISODate -> (Excel)string >
    23.更新时间：update_time   < (Mongo)ISODate -> (Excel)string >

    【 备 注 】
     验证模式：verify_mode
    （1）验证：关键字段值   ->  1
    （2）验证：关键字段值、响应字段列表 ->  2
    """
    special_list = ["interface_name", "interface_url", "request_method", "request_header", "request_params",
                    "verify_mode", "compare_core_field_name_list", "expect_core_field_value_list",
                    "expect_field_name_list", "is_depend", "depend_field_name_list", "depend_level", "case_status"]
    return special_list


def get_not_null_field_list():
    """
    【 获 取 必 填 字 段 列 表 （测试接口） 】（ 必填 ）
    01.接口名称：interface_name
    02.接口地址：interface_url
    03.请求方式：request_method
    04.验证模式：verify_mode                            （ 测试必填 ）
    05.待比较关键字段名列表：compare_core_field_name_list （ 测试必填 ）
    06.期望的关键字段值列表：expect_core_field_value_list （ 测试必填 ）
    :return:
    """
    not_null_field_list = ["interface_name", "interface_url", "request_method", "verify_mode",
                           "compare_core_field_name_list", "expect_core_field_value_list"]
    return not_null_field_list


def get_not_null_field_list_with_depend():
    """
    【 获 取 必 填 字 段 列 表（依赖接口） 】（ 必填 ）
    01.接口名称：interface_name
    02.接口地址：interface_url
    03.请求方式：request_method
    04.依赖等级：depend_level                （ 依赖必填 ）
    05.依赖字段名列表：depend_field_name_list （ 依赖必填 ）
    :return:
    """
    not_null_field_list_with_depend = ["interface_name", "interface_url", "request_method", "depend_level",
                                       "depend_field_name_list"]
    return not_null_field_list_with_depend


def get_list_field():
    """
    【 获 取 列 表 字 段 】< 表示可以通过","分割多个字段值 (Excel)string -> (Mongo)list  >
    01.待比较关键字段名列表：compare_core_field_name_list
    02.期望的关键字段值列表：expect_core_field_value_list
    03.期望的响应字段列表：expect_field_name_list
    04.依赖字段名列表：depend_field_name_list
    05.依赖字段值列表：depend_field_value_list
    06.实际的关键字段值列表：actual_core_field_value_list
    07.实际的响应字段列表：actual_field_name_list
    :return:
    """
    list_field = ["compare_core_field_name_list", "expect_core_field_value_list", "expect_field_name_list",
                  "depend_field_name_list", "depend_field_value_list",
                  "actual_core_field_value_list", "actual_field_name_list"]
    return list_field