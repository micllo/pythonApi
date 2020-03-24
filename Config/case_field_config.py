
def get_case_special_field_list():
    """
    【 获 取 excel 用 例 的 指 定 字 段 名 称 】
    01.接口名称：interface_name
    02.接口地址：interface_url
    03.请求方式：request_method
    04.请求头文件：request_header

    05.请求参数：request_params
    06.执行模式：exec_mode
    07.待比较关键字段名：compare_core_field_name
    08.期望的关键字段值：expect_core_field_value

    09.待比较响应字段列表：compare_field_name_list
    10.依赖接口名称：depend_interface
    11.依赖字段名：depend_field_name
    12.依赖字段值：depend_field_value

    13.用例状态：case_status
    14.响应信息：response_info
    15.实际的关键字段值：actual_core_field_value
    16.关键字段值比较结果：result_core_field_value

    17.响应字段列表比较结果：result_field_name_list
    18.测试结果：test_result
    19.创建时间：create_time
    20.更新时间：update_time
    :return:

    【 备 注 】
     执行模式：exec_mode
    （1）验证：关键字段值   ->  1
    （2）验证：响应字段列表 ->  2
    （3）验证上述两项      ->  3
    """
    special_list = ["interface_name", "interface_url", "request_method", "request_header",
                    "request_params", "exec_mode", "compare_core_field_name", "expect_core_field_value",
                    "compare_field_name_list", "depend_interface", "depend_field_name", "depend_field_value",
                    "case_status", "response_info", "actual_core_field_value", "result_core_field_value",
                    "result_field_name_list", "test_result", "create_time", "update_time"]
    return special_list