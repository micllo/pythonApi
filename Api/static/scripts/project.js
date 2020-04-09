/**
 *  执 行 导 入
 */
function exec_import(pro_name, nginx_api_proxy){
    swal({
        title: "确定要执行导入吗?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"

    }).then(function(isConfirm){
        if (isConfirm) {
            var file = $("#file").val().trim();
            var import_method = $("#import_method").val().trim();
            var file_suffix = file.split(".")[1]
            if(file == ""){
                swal({text: "上传文件不能为空！", type: "error", confirmButtonText: "知道了"});
            }else if(file_suffix != "xls" && file_suffix != "xlsx" && file_suffix != "csv"){
                swal({text: "文件格式不正确！（后缀必须是 .xls .xlsx .csv ）", type: "error", confirmButtonText: "知道了"});
            }else if(import_method == ""){
                swal({text: "导入方式不能为空！", type: "error", confirmButtonText: "知道了"});
            }else{
                // 获取file文件
                var file_data = new FormData($("#import_action_form")[0]);
                // 调用ajax请求(同步)
                var request_url = "/" + nginx_api_proxy + "/API/import_action/" + pro_name + "/" + import_method
                var response_info = request_interface_url_v2(url=request_url, method="POST", data=file_data, async=false, is_file=true);
                if(response_info == "请求失败"){
                    swal({text: response_info, type: "error", confirmButtonText: "知道了"});
                    $("#exec_result").html(response_info);
                    $("#exec_result").removeClass().addClass("label label-danger");
                }else{
                    var msg = response_info.msg;
                    if (msg.search("成功") != -1){
                        swal({text: msg, type: "success", confirmButtonText: "知道了"});
                        $("#exec_result").html(msg);
                        $("#exec_result").removeClass().addClass("label label-success");
                        setTimeout(function(){location.reload();}, 2000);
                    }else{
                        swal({text: msg, type: "error", confirmButtonText: "知道了"});
                        $("#exec_result").html(msg);
                        $("#exec_result").removeClass().addClass("label label-warning");
                        if (msg.search("运行中") != -1){
                            setTimeout(function(){location.reload();}, 2000);
                        }
                    }
                }
            }
            // 清空'上传文件'选项和'导入方式'下拉框
            $("#file").val("");
            $("#import_method").val("");
        }
    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });
}


/**
 *  执 行 测 试
 */
function exec_test(pro_name, nginx_api_proxy){
    swal({
        title: "确定要执行测试吗?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"

    }).then(function(isConfirm){
        // 按钮禁灰 不可点击
        // $("#test_btn").attr('disabled', true);

        if (isConfirm) {
            var host = $("#host").val().trim();
            if(host == ""){
                swal({text: "HOST 未 选 择", type: "error", confirmButtonText: "知道了"});
            }else{
                // 调用ajax请求(同步)
                var post_data = {"host": host}
                var request_url = "/" + nginx_api_proxy + "/API/run_test/" + pro_name
                var response_info = request_interface_url_v2(url=request_url, method="POST", data=post_data, async=false);
                if(response_info == "请求失败"){
                    swal({text: response_info, type: "error", confirmButtonText: "知道了"});
                    $("#result_info").html(response_info);
                    $("#result_info").removeClass().addClass("label label-danger");
                }else{
                    var msg = response_info.msg;
                    if (msg.search("测试进行中") != -1){
                        swal({text: msg, type: "success", confirmButtonText: "知道了"});
                        $("#result_info").html(msg);
                        $("#result_info").removeClass().addClass("label label-success");
                        setTimeout(function(){location.reload();}, 1000);
                    }else{
                        swal({text: msg, type: "error", confirmButtonText: "知道了"});
                        $("#result_info").html(msg);
                        $("#result_info").removeClass().addClass("label label-warning");
                        if (msg.search("运行中") != -1){
                            setTimeout(function(){location.reload();}, 2000);
                        }
                    }
                }
            }
        }
        // 清空'host'下拉框
        $("#host").val("");

    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });
}



/**
 * 修改案件状态（所有）
 */
function update_case_status_all(pro_name, case_status, nginx_api_proxy) {
    swal({
        title: "确定吗?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"

    }).then(function(isConfirm){
        if (isConfirm) {
            // 调用ajax请求(同步)
            var request_url = "/" + nginx_api_proxy + "/API/set_case_status_all/" + pro_name + "/" + case_status
            var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
            if(response_info != "请求失败"){
                setTimeout(function(){location.reload();}, 500);
            }
        }
    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });
}

/**
 * 修改案件状态（单个）
 */
function update_case_status(pro_name, nginx_api_proxy, _id) {
    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/set_case_status/" + pro_name + "/" + _id
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        if(response_info.msg.search("运行中") != -1 ){
             setTimeout(function(){location.reload();}, 500);
        }else{
            if(response_info.data.new_case_status == true){
                $("#case_status_" + _id).html("上 线");
                $("#case_status_" + _id).attr('style', "width:100px;color:#00A600;display:table-cell;vertical-align:middle;");
            }else{
                $("#case_status_" + _id).html("下 线");
                $("#case_status_" + _id).attr('style', "width:100px;color:#DC143C;display:table-cell;vertical-align:middle;");
            }
        }
    }
}


/**
 * 停止运行状态
 */
function stop_status(pro_name, nginx_api_proxy) {
    swal({
        title: "确定要停止运行状态码?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"
    }).then(function(isConfirm){
        if (isConfirm) {
            // 调用ajax请求(同步)
            var request_url = "/" + nginx_api_proxy + "/API/stop_run_status/" + pro_name
            var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
            if(response_info == "请求失败"){
                swal({text: response_info, type: "error", confirmButtonText: "知道了"});
                $("#stop_info").html(response_info);
                $("#stop_info").removeClass().addClass("label label-danger");
            }else{
                var msg = response_info.msg;
                if (msg.search("成功") != -1){
                    swal({text: msg, type: "success", confirmButtonText: "知道了"});
                    $("#stop_info").html(msg);
                    $("#stop_info").removeClass().addClass("label label-success");
                    setTimeout(function(){location.reload();}, 2000);
                }else{
                    swal({text: msg, type: "error", confirmButtonText: "知道了"});
                    $("#stop_info").html(msg);
                    $("#stop_info").removeClass().addClass("label label-warning");
                }
            }
        }
    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });
}





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

    var get_pramas = "interface_name=" + interface_name + "&request_method=" + request_method + "&interface_url=" +
        interface_url + "&case_status=" + case_status + "&is_depend=" + is_depend + "&test_result=" + test_result

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/search_case/" + pro_name + "?" + get_pramas
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var test_case_list = response_info.test_case_list;
        var case_num = response_info.case_num
        var is_run = response_info.is_run

        // 替换搜索条数
        $("#search_case_num").html("共 " + case_num + " 条");

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
            var update_time = test_case_list[i]["update_time"];

            var tr_html = "<tr>";

            // 接口名称（测试信息）
            if(is_depend){
                tr_html += "<td style=\"width: 150px; display:table-cell; vertical-align:middle;\" onclick=\"show_response_info('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" data-toggle=\"modal\" data-target=\"#show_depend_response_info\">" + interface_name + "<font color=\"#DC143C\"> (依赖) </font></td>";
            }else{
                tr_html += "<td style=\"width: 150px; display:table-cell; vertical-align:middle;\" onclick=\"show_response_info('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" data-toggle=\"modal\" data-target=\"#show_test_response_info\">" + interface_name + "</td>";
            }

            // 请求方式（请求头文件）
            tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"请求头文件\" data-content=\"" + request_header + "\">" + request_method + "</td>";

            // 接口地址（请求参数）
            tr_html += "<td style=\"width: 200px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"请求参数\" data-content=\"" + request_params + "\">" + interface_url + "</td>";

            if(is_depend){
                // 依赖字段值（依赖的字段名列表、依赖的字段值列表）
                tr_html += "<td style=\"width: 150px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"字段名：" + depend_field_name_list + "\" data-content=\"字段值：" + depend_field_value_list + "\"><span id=\"exec_result\" style=\"font-size:14px\" class=\"label label-info\">依 赖 字 段 值</span></td>";
                // 依赖等级
                tr_html += "<td class=\"text-center\"  style=\"width: 100px; display:table-cell; vertical-align:middle;\">依赖等级：" + depend_level + "</td>";
            }else{
                // 验证关键字段（期望的关键字段值）
                tr_html += "<td style=\"width: 150px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"期望的关键字段值\" data-content=\"" + expect_core_field_value_list + "\">" + compare_core_field_name_list + "</td>";
                // 验证模式（期望的响应字段列表）
                tr_html += "<td class=\"text-center\"  style=\"width: 100px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"期望的响应字段列表\" data-content=\"" + expect_field_name_list + "\">";
                if(verify_mode == 1){
                    tr_html += "仅关键字</td>";
                }else{
                    tr_html += "关键字+响应字段</td>";
                }
            }

            // 用例状态（实际的关键字段值）  onclick="update_case_status('{{pro_name}}','{{_id}}','{{nginx_api_proxy}}')" id="case_status_{{_id}}"
            if(is_depend){
                tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\" onclick=\"update_case_status('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" id=\"case_status_" + _id + "\">";
            }else{
                tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\" onclick=\"update_case_status('" + pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" id=\"case_status_" + _id + "\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"实际的关键字段值\" data-content=\"" + actual_core_field_value_list + "\">";
            }
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
            // 更新时间（实际的响应字段列表）
            if(is_depend){
                tr_html += "<td class=\"text-center\" style=\"width: 150px; display:table-cell; vertical-align:middle;\">" + update_time + "</td>";
            }else{
                tr_html += "<td class=\"text-center\" style=\"width: 150px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"实际的响应字段列表\" data-content=\"" + actual_field_name_list + "\">" + update_time + "</td>";
            }

            // 操作
            tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\">";
            if(is_run){
                tr_html += "<button class=\"btn btn-default\" type=\"button\" onclick=\"fill_edit_frame('"+ pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" data-toggle=\"modal\" data-target=\"#edit_case_form\" disabled=\"disabled\"><i class=\"fa fa-edit\" style=\"color: #6A5ACD\"></i></button>&nbsp;" +
                           "<button class=\"btn btn-default\" type=\"button\" onclick=\"del_case('"+ pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" disabled=\"disabled\"><i class=\"fa fa-trash-o fa-lg\" style=\"color: #ff0000\"></i></button>";
            }else{
                tr_html += "<button class=\"btn btn-default\" type=\"button\" onclick=\"fill_edit_frame('"+ pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" data-toggle=\"modal\" data-target=\"#edit_case_form\"><i class=\"fa fa-edit\" style=\"color: #6A5ACD\"></i></button>&nbsp;" +
                           "<button class=\"btn btn-default\" type=\"button\" onclick=\"del_case('"+ pro_name + "','" + nginx_api_proxy + "','" + _id + "')\"><i class=\"fa fa-trash-o fa-lg\" style=\"color: #ff0000\"></i></button>";
            }
            tr_html += "</td></tr>";
            tbody_html += tr_html;
        }
        $("#case_tbody").html(tbody_html);

        // 重新触发气泡弹出层功能
        $("[data-toggle='popover']").popover();
    }
}


/**
 *  新增用例
 */
function add_case(pro_name, nginx_api_proxy) {

    // 获取相应的添加内容
    var interface_name = $("#interface_name_add").val().trim();
    var interface_url = $("#interface_url_add").val().trim();
    var request_method = $("#request_method_add").val().trim();
    var request_header = $("#request_header_add").val().trim();
    var request_params = $("#request_params_add").val().trim();
    var verify_mode = $("#verify_mode_add").val().trim();
    var compare_core_field_name_list = $("#compare_core_field_name_list_add").val().trim();
    var expect_core_field_value_list = $("#expect_core_field_value_list_add").val().trim();
    var expect_field_name_list = $("#expect_field_name_list_add").val().trim();
    var is_depend = $("#is_depend_add").val().trim();
    var depend_field_name_list = $("#depend_field_name_list_add").val().trim();
    var depend_level = $("#depend_level_add").val().trim();
    var case_status = $("#case_status_add").val().trim();

    var add_dict = {"interface_name": interface_name, "interface_url": interface_url, "request_method": request_method,
        "request_header": request_header, "request_params":request_params, "verify_mode": verify_mode,
        "compare_core_field_name_list": compare_core_field_name_list, "expect_core_field_value_list": expect_core_field_value_list,
        "expect_field_name_list": expect_field_name_list, "is_depend": is_depend, "depend_level": depend_level,
        "depend_field_name_list": depend_field_name_list, "case_status": case_status};
    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/operation_case/add/" + pro_name
    var response_info = request_interface_url_v2(url=request_url, method="POST", data=add_dict, async=false);
    if(response_info == "请求失败") {
        swal({text: response_info, type: "error", confirmButtonText: "知道了"});
    }else{
        var msg = response_info.msg;
        if (msg.search("成功") != -1){
            swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
            setTimeout(function(){location.reload();}, 2000);
        }else {
            swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
        }
    }
}


/**
 *  删除用例
 */
function del_case(pro_name, nginx_api_proxy, _id) {
    swal({
        title: "确定要删除该条测试用例吗？",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"
    }).then(function(isConfirm){
        if (isConfirm) {
            var del_dict = {"_id": _id}
            // 调用ajax请求(同步)
            var request_url = "/" + nginx_api_proxy + "/API/del_case/" + pro_name
            var response_info = request_interface_url_v2(url=request_url, method="DELETE", data=del_dict, async=false);
            if(response_info == "请求失败") {
                swal({text: response_info, type: "error", confirmButtonText: "知道了"});
            }else{
                var msg = response_info.msg;
                if (msg.search("成功") != -1){
                    swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
                    setTimeout(function(){location.reload();}, 1500);
                }else {
                    swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
                    if (msg.search("运行中") != -1){
                        setTimeout(function(){location.reload();}, 2000);
                    }
                }
            }
        }
    }).catch(() => {
        console.log("cancel");
    });
}


/**
 *  填充编辑弹框（ 编辑之前 ）
 */
function fill_edit_frame(pro_name, nginx_api_proxy, _id) {

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/get_case_by_id/" + pro_name + "?_id=" + _id
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var test_case = response_info.test_case
        // 填充编辑框
        // var label = document.getElementById("case_id_edit");
        // label.innerText = _id;

        // 取消所有禁灰样式
        $("#verify_mode_edit").attr('disabled', false);
        $("#compare_core_field_name_list_edit").attr('disabled', false);
        $("#expect_core_field_value_list_edit").attr('disabled', false);
        $("#expect_field_name_list_edit").attr('disabled', false);
        $("#depend_field_name_list_edit").attr('disabled', false);
        $("#depend_level_edit").attr('disabled', false);

        // 填充内容
        $("#case_id_edit").text(_id)
        $("#interface_name_edit").val(test_case.interface_name);
        $("#interface_url_edit").val(test_case.interface_url);
        $("#request_method_edit").val(test_case.request_method);
        $("#request_header_edit").val(test_case.request_header);
        $("#request_params_edit").val(test_case.request_params);
        $("#verify_mode_edit").val(test_case.verify_mode);
        $("#compare_core_field_name_list_edit").val(test_case.compare_core_field_name_list);
        $("#expect_core_field_value_list_edit").val(test_case.expect_core_field_value_list);
        $("#expect_field_name_list_edit").val(test_case.expect_field_name_list);
        $("#depend_field_name_list_edit").val(test_case.depend_field_name_list);
        $("#depend_level_edit").val(test_case.depend_level);
        $("#case_status_edit").val(test_case.case_status);

        // 禁灰相应的样式
        if(test_case.is_depend == "True"){
            $("#is_depend_edit").text("是")
            $("#verify_mode_edit").attr('disabled', true);
            $("#compare_core_field_name_list_edit").attr('disabled', true);
            $("#expect_core_field_value_list_edit").attr('disabled', true);
            $("#expect_field_name_list_edit").attr('disabled', true);
        }else {
            $("#is_depend_edit").text("不是")
            $("#depend_field_name_list_edit").attr('disabled', true);
            $("#depend_level_edit").attr('disabled', true);
        }
    }
}



/**
 *  更新用例
 */
function edit_case(pro_name, nginx_api_proxy) {

    // 获取相应的添加内容
    var _id = $("#case_id_edit").html().trim();
    var interface_name = $("#interface_name_edit").val().trim();
    var interface_url = $("#interface_url_edit").val().trim();
    var request_method = $("#request_method_edit").val().trim();
    var request_header = $("#request_header_edit").val().trim();
    var request_params = $("#request_params_edit").val().trim();
    var verify_mode = $("#verify_mode_edit").val().trim();
    var compare_core_field_name_list = $("#compare_core_field_name_list_edit").val().trim();
    var expect_core_field_value_list = $("#expect_core_field_value_list_edit").val().trim();
    var expect_field_name_list = $("#expect_field_name_list_edit").val().trim();
    var depend_field_name_list = $("#depend_field_name_list_edit").val().trim();
    var is_depend = $("#is_depend_edit").html().trim();
    var depend_level = $("#depend_level_edit").val().trim();
    var case_status = $("#case_status_edit").val().trim();

    if(is_depend == "是"){
        is_depend = "True"
    }else {
        is_depend = "False"
    }

    var edit_dict = {"_id": _id, "interface_name": interface_name, "interface_url": interface_url, "request_method": request_method,
        "request_header": request_header, "request_params":request_params, "verify_mode": verify_mode,
        "compare_core_field_name_list": compare_core_field_name_list, "expect_core_field_value_list": expect_core_field_value_list,
        "expect_field_name_list": expect_field_name_list, "is_depend":is_depend, "depend_level": depend_level,
        "depend_field_name_list": depend_field_name_list, "case_status": case_status};
    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/operation_case/edit/" + pro_name
    var response_info = request_interface_url_v2(url=request_url, method="POST", data=edit_dict, async=false);
    if(response_info == "请求失败") {
        swal({text: response_info, type: "error", confirmButtonText: "知道了"});
    }else{
        var msg = response_info.msg;
        if (msg.search("成功") != -1){
            swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
            setTimeout(function(){location.reload();}, 1000);
        }else {
            swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
            if (msg.search("运行中") != -1){
                setTimeout(function(){location.reload();}, 2000);
            }
        }
    }
}


/**
 *  显示接口响应信息
 */
function show_response_info(pro_name, nginx_api_proxy, _id) {

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/get_case_by_id/" + pro_name + "?_id=" + _id
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
