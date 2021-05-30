# -*- coding:utf-8 -*-

# 日志、报告 等路径
LOGS_DIR = "/opt/project/logs/"
REPORTS_DIR = "/opt/project/reports/"

# 服务器地址
# SERVER_IP_PORT = "192.168.3.102"  #  MERCURY_1602
# SERVER_IP = "192.168.31.9"  # Demba Ba
SERVER_IP = "192.168.31.198"  # 旧 mac Demba Ba

# Nginx 端口
NGINX_PORT = "1180"

# Nginx中的接口反向代理名称
NGINX_API_PROXY = "api"

# 测试报告路径(Excel)
REPORT_EXCEL_PATH = "/test_report/"

# Mongo 地址
# MONGODB_ADDR = "192.168.31.9:27077"
MONGODB_ADDR = "192.168.31.198:27077"  # 旧 mac Demba Ba

# 上传的临时用例目录
UPLOAD_CASE_DIR = "/opt/project/tmp/"


############################################# 相 同 的 配 置 #############################################


# 接口地址( uwsgi )
API_ADDR = SERVER_IP + ":" + NGINX_PORT + "/" + NGINX_API_PROXY

# 测试报告地址(Excel)
BASE_REPORT_EXCEL_PATH = "http://" + SERVER_IP + ":" + NGINX_PORT + REPORT_EXCEL_PATH

# 测试报告地址(HTML)
TEST_REPORT_URL = API_ADDR + "/API/get_test_report/"

# Mongo 数据库
MONGODB_DATABASE = "api_auto_test"
TABLE_CASE = "_case"
TABLE_CONFIG = "_config"
TABLE_RESULT = "_result"

# 上传的临时用例文件
UPLOAD_CASE_FILE = UPLOAD_CASE_DIR + "upload_case_file.xlsx"

# 构建的时候使用前端静态文件路径 ( Api/__init__.py文件的同级目录 ) 'static'、'templates'
GULP_STATIC_PATH = '../Build'
GULP_TEMPLATE_PATH = '../Build/templates'

# 邮箱配置参数(发送者)
ERROR_MAIL_HOST = "smtp.163.com"
ERROR_MAIL_ACCOUNT = "miclloo@163.com"
ERROR_MAIL_PASSWD = "qweasd123"  # 客户端授权密码，非登录密码

# 报错邮箱地址(接收者)
MAIL_LIST = ["micllo@126.com"]

# 钉钉通知群
DD_MONITOR_GROUP = "3a2069108f0775762cbbfea363984c9bf59fce5967ada82c78c9fb8df354a624"
DD_AT_PHONES = "13816439135,18717854213"
DD_AT_FXC = "13816439135"
