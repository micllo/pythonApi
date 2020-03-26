# -*- coding:utf-8 -*-
from Common.com_func import send_mail, send_DD, log


def mongo_exception_send_DD(e, msg):
    """
    发现异常时钉钉通知
    :param e:
    :param msg:
    :return:
    """
    title = "[监控]'mongo'操作通知"
    text = "#### WEB自动化测试'mongo'操作错误\n\n****操作方式：" + msg + "****\n\n****错误原因：" + str(e) + "****"
    send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title=title, text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)

