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
 * 搜索用例
 */
function search_case(pro_name, nginx_api_proxy) {

     // 获取相应的搜索内容
    var interface_name = $("#interface_name").val().trim();
    var request_method = $("#request_method").val().trim();
    var interface_url = $("#interface_url").val().trim();
    var case_status = $("#case_status").val().trim();

    var get_pramas = "interface_name=" + interface_name + "&request_method=" + request_method + "&interface_url=" +
        interface_url + "&case_status=" + case_status

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/search_case/" + pro_name + "?" + get_pramas
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var test_case_list = response_info.test_case_list;

        // 重新渲染table页面 <tbody id="case_tbody">
        var tbody_html = "";
        for (var i = 0; i < test_case_list.length; i++){
            var _id = test_case_list[i]["_id"];
            var interface_name = test_case_list[i]["interface_name"];
            var interface_url = test_case_list[i]["interface_url"];
            var request_method = test_case_list[i]["request_method"];
            var request_params = test_case_list[i]["request_params"];
            var compare_core_field_name = test_case_list[i]["compare_core_field_name"];
            var expect_core_field_value = test_case_list[i]["expect_core_field_value"];
            var expect_field_name_list = test_case_list[i]["expect_field_name_list"];
            var verify_mode = test_case_list[i]["verify_mode"];
            var case_status = test_case_list[i]["case_status"];
            var update_time = test_case_list[i]["update_time"];

            var tr_html = "<tr>" +
                "<td style=\"width: 150px; display:table-cell; vertical-align:middle;\">" + interface_name + "</td>" +
                "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\">" + request_method + "</td>" +
                "<td style=\"width: 250px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"请求参数\" data-content=\"" + request_params + "\">" + interface_url + "</td>" +
                "<td class=\"text-center\"  style=\"width: 100px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"期望的关键字段值\" data-content=\"" + expect_core_field_value + "\">" + compare_core_field_name + "</td>" +
                "<td class=\"text-center\"  style=\"width: 100px; display:table-cell; vertical-align:middle;\" data-toggle=\"popover\" data-trigger=\"hover\" data-placement=\"bottom\" data-container=\"body\" title=\"期望的响应字段列表\" data-content=\"" + expect_field_name_list + "\">" + verify_mode + "</td>";
            if(case_status){
                tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\"><font color=\"#00A600\">上线</font></td>";
            }else{
                tr_html += "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\"><font color=\"#DC143C\">下线</font></td>";
            }
            tr_html += "<td class=\"text-center\" style=\"width: 150px; display:table-cell; vertical-align:middle;\">" + update_time + "</td>" +
                "<td class=\"text-center\" style=\"width: 100px; display:table-cell; vertical-align:middle;\">" +
                "<button class=\"btn btn-default\" type=\"button\" onclick=\"fill_edit_frame('"+ pro_name + "','" + nginx_api_proxy + "','" + _id + "')\" data-toggle=\"modal\" data-target=\"#edit_case_form\"><i class=\"fa fa-edit\" style=\"color: #6A5ACD\"></i></button>&nbsp;" +
                "<button class=\"btn btn-default\" type=\"button\" onclick=\"del_case('"+ pro_name + "','" + nginx_api_proxy + "','" + _id + "')\"><i class=\"fa fa-trash-o fa-lg\" style=\"color: #ff0000\"></i></button>" +
                "</td>" +
                "</tr>";
            tbody_html += tr_html;
        }
        $("#case_tbody").html(tbody_html);

        // 需要重新触发气泡弹出层
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
    var compare_core_field_name = $("#compare_core_field_name_add").val().trim();
    var expect_core_field_value = $("#expect_core_field_value_add").val().trim();
    var expect_field_name_list = $("#expect_field_name_list_add").val().trim();
    var depend_interface = $("#depend_interface_add").val().trim();
    var depend_field_name = $("#depend_field_name_add").val().trim();
    var depend_field_value = $("#depend_field_value_add").val().trim();
    var case_status = $("#case_status_add").val().trim();

    var add_dict = {"interface_name": interface_name, "interface_url": interface_url, "request_method": request_method,
        "request_header": request_header, "request_params":request_params, "verify_mode": verify_mode,
        "compare_core_field_name": compare_core_field_name, "expect_core_field_value": expect_core_field_value,
        "expect_field_name_list": expect_field_name_list, "depend_interface": depend_interface,
        "depend_field_name": depend_field_name, "depend_field_value": depend_field_value, "case_status": case_status};
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
            var response_info = request_interface_url_v2(url=request_url, method="POST", data=del_dict, async=false);
            if(response_info == "请求失败") {
                swal({text: response_info, type: "error", confirmButtonText: "知道了"});
            }else{
                var msg = response_info.msg;
                if (msg.search("成功") != -1){
                    swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
                    setTimeout(function(){location.reload();}, 1500);
                }else {
                    swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
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
        $("#case_id_edit").text(_id)
        $("#interface_name_edit").val(test_case.interface_name);
        $("#interface_url_edit").val(test_case.interface_url);
        $("#request_method_edit").val(test_case.request_method);
        $("#request_header_edit").val(test_case.request_header);
        $("#request_params_edit").val(test_case.request_params);
        $("#verify_mode_edit").val(test_case.verify_mode);
        $("#compare_core_field_name_edit").val(test_case.compare_core_field_name);
        $("#expect_core_field_value_edit").val(test_case.expect_core_field_value);
        $("#expect_field_name_list_edit").val(test_case.expect_field_name_list);
        $("#depend_interface_edit").val(test_case.depend_interface);
        $("#depend_field_name_edit").val(test_case.depend_field_name);
        $("#depend_field_value_edit").val(test_case.depend_field_value);
        $("#case_status_edit").val(test_case.case_status);
    }
}



/**
 *  编辑用例
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
    var compare_core_field_name = $("#compare_core_field_name_edit").val().trim();
    var expect_core_field_value = $("#expect_core_field_value_edit").val().trim();
    var expect_field_name_list = $("#expect_field_name_list_edit").val().trim();
    var depend_interface = $("#depend_interface_edit").val().trim();
    var depend_field_name = $("#depend_field_name_edit").val().trim();
    var depend_field_value = $("#depend_field_value_edit").val().trim();
    var case_status = $("#case_status_edit").val().trim();

    var edit_dict = {"_id": _id, "interface_name": interface_name, "interface_url": interface_url, "request_method": request_method,
        "request_header": request_header, "request_params":request_params, "verify_mode": verify_mode,
        "compare_core_field_name": compare_core_field_name, "expect_core_field_value": expect_core_field_value,
        "expect_field_name_list": expect_field_name_list, "depend_interface": depend_interface,
        "depend_field_name": depend_field_name, "depend_field_value": depend_field_value, "case_status": case_status};
    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/API/operation_case/edit/" + pro_name
    var response_info = request_interface_url_v2(url=request_url, method="POST", data=edit_dict, async=false);
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
