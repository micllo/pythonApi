
/**
 * 搜索用例
 */
function search_case(pro_name, nginx_api_proxy) {

    // 隐藏之前已经弹出的气泡弹层
    $("[data-toggle='popover']").popover('hide');

     // 获取相应的搜索内容
    var interface_name = $("#interface_name").val().trim();
    var request_method = $("#request_method").val().trim();
    var interface_url = $("#interface_url").val().trim();
    var case_status = $("#case_status").val().trim();
    var is_depend = $("#is_depend").val().trim();
    var test_result = $("#test_result").val().trim();
    var test_time = $("#test_time").val().trim();

    var get_pramas = "interface_name=" + interface_name + "&request_method=" + request_method + "&interface_url=" +
    interface_url + "&case_status=" + case_status + "&is_depend=" + is_depend + "&test_result=" + test_result +
    "&test_time=" + test_time

    // 报告页面 需要更新 统计数据
    var r_url = "/" + nginx_api_proxy + "/API/query_statist_data/" + pro_name + "?test_time=" + test_time
    var r_info = request_interface_url_v2(url=r_url, method="GET", async=false);
    if(r_info != "请求失败") {
        var statist_data = r_info.statist_data;
        console.log(statist_data)
        $("#depend_num").html(statist_data['depend']);
        $("#test_num").html(statist_data['test']);
        $("#all_num").html(statist_data['test']);
        $("#success_num").html(statist_data['success']);
        $("#fail_num").html(statist_data['fail']);
        $("#error_num").html(statist_data['error']);
    }

    // 两个页面 公共搜索操作部分
    var request_url = "/" + nginx_api_proxy + "/API/search_case/" + pro_name + "/_result?" + get_pramas
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var test_case_list = response_info.test_case_list;
        var case_num = response_info.case_num
        // var is_run = response_info.is_run

        // 替换搜索条数
        $("#search_case_num").html("共 " + case_num + " 条");

        if(test_case_list[0]){
            // 替换 查看当前host 模态框
            $("#current_host").html(test_case_list[0]["host"]);

            // 替换 查看当前全局变量 模态框 <div id="current_global_variable" class="modal-body">
            var cgv_html = "";
            var global_variable_dict = test_case_list[0]["global_variable_dict"];
            for (var key in global_variable_dict){
                var div_html = "<div class=\"form-group\" style=\"margin-top:5px\">";
                div_html += "<label style=\"margin-left:5px;font-size:20px;\" class=\"text-info\"><font color=\"#5B00AE\">" + key + "</font>&nbsp;&nbsp;->&nbsp;&nbsp;" + global_variable_dict[key] + "</label>";
                div_html += "</div>";
                cgv_html += div_html;
            }
            $("#current_global_variable").html(cgv_html);
        }

        // 重新渲染table页面 <tbody id="case_tbody">
        var tbody_html = "";
        for (var i = 0; i < test_case_list.length; i++){
            var _id = test_case_list[i]["_id"];
            var interface_name = test_case_list[i]["interface_name"];
            var interface_url = test_case_list[i]["interface_url"];
            var request_method = test_case_list[i]["request_method"];
            var request_header = test_case_list[i]["request_header"];
            var request_params = test_case_list[i]["request_params"];
            var compare_core_field_name_list = test_case_list[i]["compare_core_field_name_list"];
            var expect_core_field_value_list = test_case_list[i]["expect_core_field_value_list"];
            var expect_field_name_list = test_case_list[i]["expect_field_name_list"];
            var verify_mode = test_case_list[i]["verify_mode"];
            var is_depend = test_case_list[i]["is_depend"];
            var depend_level = test_case_list[i]["depend_level"];
            var depend_field_name_list = test_case_list[i]["depend_field_name_list"];
            var depend_field_value_list = test_case_list[i]["depend_field_value_list"];
            var actual_core_field_value_list = test_case_list[i]["actual_core_field_value_list"];
            var actual_field_name_list = test_case_list[i]["actual_field_name_list"];
            var case_status = test_case_list[i]["case_status"];
            var test_result = test_case_list[i]["test_result"];
            var exec_time = test_case_list[i]["exec_time"];
            var tr_html = "<tr>";

            // 接口名称（测试信息）
            if(is_depend){
                tr_html += "<td style=\"width: 150px; color:#4D0000; display:table-cell; vertical-align:middle;\" onclick=\"show_response_info('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "','_result')\" data-toggle=\"modal\" data-target=\"#show_depend_response_info\">" + interface_name + "<font color=\"#BB5E00\"> (依赖) </font></td>";
            }else{
                tr_html += "<td style=\"width: 150px; color:#4D0000; display:table-cell; vertical-align:middle;\" onclick=\"show_response_info('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "','_result')\" data-toggle=\"modal\" data-target=\"#show_test_response_info\">" + interface_name + "</td>";
            }

            // 请求方式（请求头文件）
            tr_html += "<td class=\"text-center\" style=\"width: 100px; color:#4D0000; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"请求头文件\" data-content=\"" + request_header + "\">" + request_method + "</td>";

            // 接口地址（请求参数）
            tr_html += "<td style=\"width: 150px; color:#4D0000; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"请求参数\" data-content=\"" + request_params + "\">" + interface_url + "</td>";

            if(is_depend){
                // 依赖字段值（依赖的字段名列表、依赖的字段值列表）
                tr_html += "<td style=\"width: 150px; color:#4D0000; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"字段名：" + depend_field_name_list + "\" data-content=\"字段值：" + depend_field_value_list + "\"><span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-info\">依 赖 字 段 值</span></td>";
                // 依赖等级
                tr_html += "<td class=\"text-center\" style=\"width: 100px; color:#4D0000; display:table-cell; vertical-align:middle;\">依赖等级：" + depend_level + "</td>";
            }else{
                // 验证关键字段（期望的关键字段值）
                tr_html += "<td style=\"width: 150px; color:#4D0000; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"期望的关键字段值\" data-content=\"" + expect_core_field_value_list + "\">" + compare_core_field_name_list + "</td>";
                // 验证模式
                tr_html += "<td class=\"text-center\" style=\"width: 100px; color:#4D0000; display:table-cell; vertical-align:middle;\">";
                if(verify_mode == 1){
                    tr_html += "仅关键字段</td>";
                }else{
                    tr_html += "关键字段+响应字段列表</td>";
                }
            }

            // 用例状态
            tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\" onclick=\"update_case_status('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" id=\"case_status_" + _id + "\">";
            if(case_status){
                tr_html += "<font color=\"#00A600\">上线</font></td>";
            }else{
                tr_html += "<font color=\"#DC143C\">下线</font></td>";
            }

            // 测试结果（测试结果信息）
            tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"测试结果信息\" data-content=\"" + test_result + "\">";
            if(is_depend){
                if(test_result.search("success") != -1){
                    tr_html += "<font color=\"#00A600\"> 依赖成功 </font>";
                }else if(test_result.search("fail") != -1){
                    tr_html += "<font color=\"#DC143C\"> 依赖失败 </font>";
                }else if(test_result.search("error") != -1){
                    tr_html += "<font color=\"#C6A300\"> 配置错误 </font>";
                }else{
                }
            }else{
                if(test_result.search("依赖") != -1){
                tr_html += "<span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-warning\"> 依赖错误 </span></td>";
                }else if(test_result.search("success") != -1){
                    tr_html += "<span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-success\"> 测试成功 </span></td>";
                }else if(test_result.search("fail") != -1){
                    tr_html += "<span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-danger\"> 测试失败 </span></td>";
                }else if(test_result.search("error") != -1){
                    tr_html += "<span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-warning\"> 配置错误 </span></td>";
                }else{
                    tr_html += "<span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-info\"></span></td>";
                }
            }
            // 测试时间
            tr_html += "<td class=\"text-center\" style=\"width: 150px; color:#4D0000; display:table-cell; vertical-align:middle;\">" + exec_time + "</td>";

            tr_html += "</td></tr>";
            tbody_html += tr_html;
        }
        $("#case_tbody").html(tbody_html);

        // 重新触发气泡弹出层功能
        $("[data-toggle='popover']").popover();
    }
}


/**
 *  显示接口响应信息
 */
function show_response_info(pro_name, nginx_api_proxy, _id, table_tag) {

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/get_case_by_id/" + pro_name + "/" + table_tag + "?_id=" + _id
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var test_case = response_info.test_case

        // 填充内容
        if(test_case.is_depend == "True"){
            $("#case_id_show_depend").text(_id)
            $("#is_depend_show_depend").text(test_case.is_depend)
            $("#interface_name_show_depend").text(test_case.interface_name);
            $("#interface_url_show_depend").text(test_case.interface_url);
            $("#request_method_show_depend").text(test_case.request_method);
            $("#request_header_show_depend").text(test_case.request_header);
            $("#request_params_show_depend").text(test_case.request_params);
            $("#case_status_show_depend").text(test_case.case_status);
            $("#response_info_show_depend").text(test_case.response_info)
            $("#depend_level_show_depend").text(test_case.depend_level);
            $("#depend_field_name_list_show_depend").text(test_case.depend_field_name_list);
            $("#depend_field_value_list_show_depend").text(test_case.depend_field_value_list);
            $("#depend_level_show_depend").text(test_case.depend_level);
            $("#test_result_show_depend").text(test_case.test_result);
            $("#run_status_show_depend").text(test_case.run_status);
            $("#create_time_show_depend").text(test_case.create_time);
            $("#update_time_show_depend").text(test_case.update_time);

            if(test_case.test_result.search("success") != -1){
                $("#test_result_show_depend").attr('style', "color:#00A600");
            }else if(test_case.test_result.search("fail") != -1){
                $("#test_result_show_depend").attr('style', "color:#DC143C");
            }else{  // error
                $("#test_result_show_depend").attr('style', "color:#C6A300");
            }

        }else{
            $("#case_id_show_test").text(_id)
            $("#is_depend_show_test").text(test_case.is_depend)
            $("#interface_name_show_test").text(test_case.interface_name);
            $("#interface_url_show_test").text(test_case.interface_url);
            $("#request_method_show_test").text(test_case.request_method);
            $("#request_header_show_test").text(test_case.request_header);
            $("#request_params_show_test").text(test_case.request_params);
            $("#case_status_show_test").text(test_case.case_status);
            $("#response_info_show_test").text(test_case.response_info);
            $("#verify_mode_show_test").text(test_case.verify_mode);
            $("#compare_core_field_name_list_show_test").text(test_case.compare_core_field_name_list);
            $("#expect_core_field_value_list_show_test").text(test_case.expect_core_field_value_list);
            $("#actual_core_field_value_list_show_test").text(test_case.actual_core_field_value_list);
            $("#result_core_field_value_show_test").text(test_case.result_core_field_value);
            $("#expect_field_name_list_show_test").text(test_case.expect_field_name_list);
            $("#actual_field_name_list_show_test").text(test_case.actual_field_name_list);
            $("#result_field_name_list_show_test").text(test_case.result_field_name_list);
            $("#test_result_show_test").text(test_case.test_result)
            $("#run_status_show_test").text(test_case.run_status)
            $("#create_time_show_test").text(test_case.create_time);
            $("#update_time_show_test").text(test_case.update_time);

            if(test_case.result_core_field_value.search("pass") != -1){
                $("#result_core_field_value_show_test").attr('style', "color:#00A600");
            }else{  // fail
                $("#result_core_field_value_show_test").attr('style', "color:#DC143C");
            }

            if(test_case.result_field_name_list.search("pass") != -1){
                $("#result_field_name_list_show_test").attr('style', "color:#00A600");
            }else{  // fail
                $("#result_field_name_list_show_test").attr('style', "color:#DC143C");
            }

            if(test_case.test_result.search("success") != -1){
                $("#test_result_show_test").attr('style', "color:#00A600");
            }else if(test_case.test_result.search("fail") != -1){
                $("#test_result_show_test").attr('style', "color:#DC143C");
            }else{  // error
                $("#test_result_show_test").attr('style', "color:#C6A300");
            }

        }

    }
}


/**
 *  通过'运行方式'下拉框 筛选 '测试时间'
 */
function screen_test_time(pro_name, nginx_api_proxy) {
    // 获取选中的下拉框 key , value
    var selectedOption = $("#run_type option:selected");
    console.log(selectedOption.val(), selectedOption.text());
    var option_val = selectedOption.val();
    var option_text = selectedOption.text();
    var request_url = "/" + nginx_api_proxy + "/API/screen_test_time/" + pro_name + "?run_type=" + option_val
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败") {
        var test_time_list = response_info.test_time_list
        // 替换 测试时间 下拉框 <select id="test_time">
        var option_html = "";
        console.log(test_time_list)
        console.log(test_time_list.length == 0)
        console.log(test_time_list.length)
        if (test_time_list.length == 0){
            option_html += "<option value=\"\">暂无数据</option>";
        }else{
            for (var i = 0; i < test_time_list.length; i++){
                option_html += "<option value=\"" + test_time_list[i] + "\">" + test_time_list[i] + "</option>";
            }
        }
        $("#test_time").html(option_html);
    }
}
