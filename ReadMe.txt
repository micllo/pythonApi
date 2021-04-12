
【 注 意 事 项 】
1.新增项目时
（1）项目页面新增"host"选项
（2）需要在'Config > pro_config.py'文件中
     1) 配置 项目对应的 HOST
     2) 配置 项目对应的服务器地址

2.导入用例时
（1）必填项：是否为依赖接口、接口名称、接口地址、请求方式
（2）测试必填项：验证模式、待比较关键字段名列表、期望的关键字段值列表
（3）依赖必填项：依赖字段名列表、依赖等级
（4）Excel中的'验证模式、依赖等级'：必须是数字类型、或者可以为空
（5）Excel中的'是否为依赖接口、用例状态'：必须是布尔类型、或者可以为空
（6）相关'xxx列表'字段：若有多个必须使用英文逗号隔开
（7）需要替换的依赖变量：前后必须使用'{{' 和 '}}'做标记


########################################################################################################################


【 本 地 配 置 项 目 开 发 环 境 】

1.配置本地 venv 虚拟环境
（1）修改：requirements_init.txt
（2）删除：原有 venv 目录
（3）执行：sh -x venv_install.sh

2.配置 gulpfile 依赖
（1）修改：gulpfile_install.sh
（2）删除：原有的 package.json 文件
（3）执行：sh -x gulpfile_install.sh

3.配置 Nginx -> python_api.conf

upstream api_server_API{
  server 127.0.0.1:7071 weight=1 max_fails=2 fail_timeout=30s;
  ip_hash;
}

server {
  listen 7060;
  server_name localhost;

  location /api_case_tmpl {
        sendfile off;
        expires off;
        gzip on;
        gzip_min_length 1000;
        gzip_buffers 4 8k;
        gzip_types application/json application/javascript application/x-javascript text/css application/xml;
        add_header Cache-Control no-cache;
        add_header Cache-Control 'no-store';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        alias /Users/micllo/Documents/works/GitHub/pythonApi/api_case_tmpl.xlsx;
       }

  location /test_report_local/ {
        sendfile off;
        expires off;
        gzip on;
        gzip_min_length 1000;
        gzip_buffers 4 8k;
        gzip_types application/json application/javascript application/x-javascript text/css application/xml;
        add_header Cache-Control no-cache;
        add_header Cache-Control 'no-store';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        alias /Users/micllo/Documents/works/GitHub/pythonApi/Reports/;
       }

  location /api_local/ {
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header REMOTE-HOST $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504 http_404;
         proxy_pass http://api_server_API/;
         #proxy_pass http://127.0.0.1:7071/;
         proxy_redirect default;
  }
}


【 备 注 】
MAC本地安装的 nginx 相关路径
默认安装路径：/usr/local/Cellar/nginx/1.15.5/
默认配置文件路径：/usr/local/etc/nginx/
sudo nginx
sudo nginx -t
sudo nginx -s reload

########################################################################################################################


【 本地 Mac 相关 】

1.uWSGI配置文件：./vassals/mac_app_uwsgi.ini
（1）启动 uWSGI 命令 在 ./start_uwsgi_local.sh 脚本
（2）停止 uWSGI 命令 在 ./stop_uwsgi.sh 脚本

2.上传 GitHub 需要被忽略的文件
（1）Logs、Reports -> 临时生产的 日志、报告
（2）vassals_local、venv -> 本地的 uWSGI配置、python3虚拟环境
（3）node_modules、gulpfile.js、package.json、package-lock.json -> 供本地启动使用的gulp工具

3.访问地址（ server.py 启动 ）：
（1）接口地址 -> http://127.0.0.1:7072/
               http://127.0.0.1:7072/API/index
               http://127.0.0.1:7072/API/get_project_case_list/<pro_name>

4.访问地址（ uwsgi 启动 ）：
（1）用例模板 -> http://localhost:7060/api_case_tmpl
（2）测试报告 -> http://localhost:7060/test_report_local/<pro_name>/[API_report]<pro_name>.xls
（3）页面首页 -> http://localhost:7060/api_local/API/index
（4）接口地址 -> http://localhost:7060/api_local/API/xxxxxxx
   （ 备注：uwgsi 启动 7071 端口、nginx 配置 7060 反向代理 7071 ）

5.本地相关服务的启动操作（ gulpfile.js 文件 ）
（1）启动服务并调试页面：gulp "html debug"
（2）停止服务命令：gulp "stop env"
（3）部署docker服务：gulp "deploy docker"


【 虚拟环境添加依赖 】
1.创建虚拟环境：virtualenv -p /usr/local/bin/python3 venv （-p：指明python3所在目录）
2.切换到虚拟环境：source venv/bin/activate
3.退出虚拟环境：deactivate
4.添加依赖：
pip3 install -v flask==0.12 -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com


########################################################################################################################


【 Docker Centos7 相关 】

1.uWSGI配置文件：vassals_docker/app_uwsgi.ini
（1）启动 uWSGI 命令 在 ./start_uwsgi.sh 脚本
（2）停止 uWSGI 命令 在 ./stop_uwsgi.sh 脚本

2.服务器目录结构
  /var/log/uwsgi/ 		   -> pid_uwsgi.pid、app_uwsgi.log、emperor.log
  /var/log/nginx/ 		   -> error.log、access.log
  /etc/uwsgi/vassals/	   -> app_uwsgi.ini
  /opt/project/logs/ 	   -> 项目日志
  /opt/project/reports/	   -> 测试报告
  /opt/project/${pro_name} -> 项目
  /opt/project/tmp         -> 临时目录(部署时使用)

3.服务器部署命令：
（1）从GitGub上拉取代码至临时目录
（2）关闭nginx、mongo、uwsgi服务
（3）替换项目、uwsgi.ini配置文件
（4）替换env_config配置文件
（5）启动nginx、mongo、uwsgi服务
（6）清空临时文件

4.部署时的存放位置：
（1）./pythonApi -> /opt/project/pythonApi
（2）./pythonApi/vassals/app_uwsgi.ini -> /etc/uwsgi/vassals/app_uwsgi.ini

5.部署时相关配置文件的替换操作：
（1）将./Env/目录下的 env_config.py 删除
（2）将./Env/目录下的 env_config_docker.py 重命名为 env_config.py

6.访问地址（ Docker 内部 ）：
（1）用例模板 -> http://127.0.0.1:80/api_case_tmpl
（2）测试报告 -> http://127.0.0.1:80/test_report/<pro_name>/[API_report]<pro_name>.xls
（3）页面首页 -> http://127.0.0.1:80/api/API/index
（4）接口地址 -> http://127.0.0.1:80/api/API/xxxxxxx
    ( 备注：uwgsi 启动 8081 端口、nginx 配置 80 反向代理 8081 )

7.访问地址（ 外部访问 ）：
（1）用例模板 -> http://192.168.31.9:1180/api_case_tmpl
（2）测试报告 -> http://192.168.31.9:1180/test_report/<pro_name>/[API_report]<pro_name>.xls
（3）页面首页 -> http://192.168.31.9:1180/api/API/index
（4）接口地址 -> http://192.168.31.9:1180/api/API/xxxxxxx
    ( 备注：docker 配置 1180 映射 80 )

8.关于部署
  通过'fabric'工具进行部署 -> deploy.py
    （1）将本地代码拷贝入临时文件夹，并删除不需要的文件目录
    （2）将临时文件夹中的该项目压缩打包，上传至服务器的临时文件夹中
    （3）在服务器中进行部署操作：停止nginx、mongo、uwsgi服务 -> 替换项目、uwsgi.ini配置文件 -> 替换config配置文件 -> 启动nginx、mongo、uwsgi服务
    （4）删除本地的临时文件夹
  'gulp'命令 执行 deploy.py 文件 进行部署


########################################################################################################################


【 框 架 结 构 】（ 提高代码的：可读性、重用性、易扩展性 ）
 1.Api层：       对外接口、原静态文件
 2.Build层：     编译后的静态文件
 3.Common层：    通用方法、获取依赖变量类、验证接口类
 4.Config层：    用例字段配置、错误码映射、定时任务、项目配置
 5.Env层：       环境配置
 6.Tools层：     工具函数
 7.其他：
 （1）tmp/ -> 临时存放上传的用例Excel文件
 （2）api_case_tmpl.xlsx  -> 供页面下载的测试用例模板文件
 （3）vassals/ -> 服务器的'uWSGI配置'
 （4）vassals_local/、venv/ -> 本地的'uWSGI配置、python3虚拟环境'
 （5）Logs/、Reports/、Screenshot/ -> 临时生产的 日志、报告、截图
 （6）node_modules/、gulpfile.js、package.json、package-lock.json -> 供本地启动使用的gulp工具
 （7）deploy.py、start_uwsgi_local.sh、stop_uwsgi_local.sh、tmp_uwsgi_pid.txt -> 本地部署文件及相关命令和临时文件


【 功 能 点 】

1.项目用途
（1）接口的文档管理
（2）接口的定时监控（生产环境）
（3）接口的自动化回归测试（测试环境）

2.页面功能、定时任务
（1）[页面] 下载接口测试用例模板(Excel)
（2）[页面] 批量导入(新增、替换)、增删改查 测试用例
（3）[页面] 下载测试报告(Excel)：成功的用例、失败的用例、错误的用例、依赖的用例、未执行的用例
（4）[页面] 批量执行测试、用例上下线
（5）[页面] 显示用例相关信息：接口名称、接口地址、请求方式、请求参数、响应信息、待验证的关键字、待验证的响应字段列表、测试结果 等
（6）[定时任务] 删除过期(一周前)的文件：日志、报告
（7）[定时任务] 生成报告(每天一次)
（8）[定时任务] 执行接口测试(每天n次)

3.验证模式
（1）验证关键字段：验证期望的关键字段值是否正确
（2）验证响应字段列表：验证期望的响应字段名列表是否正确

4.依赖逻辑
（1）若测试接口需要依赖某接口返回的某个字段值，则先执行依赖接口，通过 {{ field }} 的形式进行匹配捕获并替换
（2）若存在多个依赖接口，且依赖接口之间也存在依赖关系的情况，则通过设置'依赖等级'来控制依赖接口的调用顺序
（3）若某个依赖接口未请求成功的话，则所有测试接口的测试结果都记录为'依赖接口的问题'

5.请求失败重试逻辑
（1）通过装饰器，循环执行请求
（2）若请求失败的，则最多重试3次


【 框 架 工 具 】
 Python3 + Flask + uWSGI + Nginx + Bootstrap + MongoDB + Docker + Fabric + Gulp

1.使用 Flask ：
（1）提供 相关测试接口、页面接口

2.使用 Nginx ：
（1）提供 用例模板、最新报告 的下载地址
（2）反向代理 相关接口

3.使用 uWSGI :
（1）用作 web 服务器
（2）使用'emperor'命令进行管理：监视和批量启停 vassals 目录下 uwsgi 相关的 .ini 文件

4.使用 Docker：
（1）使用Dockerfile构建centos7镜像：提供项目所需的相关配置环境
（2）使用'docker-compose' 一键管理多个容器

5.使用 MongoDB ：
（1）保存测试用例

6.使用 Fabric ：
（1）配置相关脚本，实现一键部署

7.使用 NodeJS 的 Gulp 命令 ：
（1）配置本地启动的相关服务，实现一键启动或停止
（2）编译静态文件，防止浏览器缓存js问题
（3）实时监听本地调试页面功能

