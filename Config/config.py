# -*- coding:utf-8 -*-

# 日志、报告、截图 等路径
LOGS_PATH = "/Users/micllo/Documents/works/GitHub/pythonApi/Logs/"
REPORTS_PATH = "/Users/micllo/Documents/works/GitHub/pythonApi/Reports/"

# 服务器地址
SERVER_IP = "127.0.0.1"

# Nginx 端口
NGINX_PORT = "7060"

# Nginx中的接口反向代理名称
NGINX_API_PROXY = "api_local"

# 保存上传的用例文件
UPLOAD_CASE_FILE = "/Users/micllo/Documents/works/GitHub/pythonApi/tmp/upload_case_file.xlsx"


############################################# 相 同 的 配 置 #############################################

# 邮箱配置参数
ERROR_MAIL_HOST = "smtp.163.com"
ERROR_MAIL_ACCOUNT = "miclloo@163.com"
ERROR_MAIL_PASSWD = "qweasd123"  # 客户端授权密码，非登录密码

# 构建的时候使用前端静态文件路径 ( Api/__init__.py文件的同级目录 ) 'static'、'templates'
GULP_STATIC_PATH = '../Build'
GULP_TEMPLATE_PATH = '../Build/templates'

# 测试报告地址
BASE_REPORT_PATH = "http://" + SERVER_IP + ":" + NGINX_PORT + "/test_report_local/"
CURRENT_REPORT_URL = BASE_REPORT_PATH + "report.html"
HISTORY_REPORT_PATH = BASE_REPORT_PATH + "history/"

# 接口地址( uwsgi )
API_ADDR = SERVER_IP + ":" + NGINX_PORT + "/" + NGINX_API_PROXY

# mongo 数据库
MONGODB_ADDR = SERVER_IP + ":27017"
MONGODB_DATABASE = "api_auto_test"

# 报错邮箱地址
MAIL_LIST = ["micllo@126.com"]

# 钉钉通知群
DD_MONITOR_GROUP = "3a2069108f0775762cbbfea363984c9bf59fce5967ada82c78c9fb8df354a624"
DD_AT_PHONES = "13816439135,18717854213"
DD_AT_FXC = "13816439135"
