# -*- coding: utf-8 -*-
"""
装饰器
"""
import time
from Tools.log import FrameLog
from Tools.date_helper import current_timestamp
from threading import Thread
import threading
from functools import wraps
from Env import env_config as cfg
from Config.pro_config import get_pro_name

save_mutex = threading.Lock()
log = FrameLog().log()


def retry_request(try_limit=3, interval_time=1, log_show=True, send_dd=False):
    """
    接口重试
    :param try_limit:
    :param interval_time:
    :param log_show:
    :param send_dd:
    :param send_flag:
    :return:

     备注：若重试全部失败后，返回 31500
    """
    def try_func(func):
        def wrapper(*args, **kwargs):
            try_cnt = 0
            while try_cnt < try_limit:
                try:
                    st = time.time()
                    res = func(*args, **kwargs)
                    et = time.time()
                    if log_show:
                        log.info("%s: DONE %s" % (func.__name__, (et-st)))
                    return res
                except Exception as e:
                    time.sleep(interval_time)
                    try_cnt += 1
                    if log_show:
                        log.error(e)
                        log.warning("%s: RETRY CNT %s" % (func.__name__, try_cnt))
            if log_show:
                log.warning("%s: FAILED" % func.__name__)
            if send_dd:
                # log.info("interface_url -> " + str(kwargs.get("interface_url", "")))
                pro_name, server_ip = get_pro_name(str(kwargs.get("interface_url", "")))
                from Common.com_func import send_DD
                text = "#### [API]'" + pro_name + "' 项目测试请求 - 接口无响应，服务器iP: " + server_ip
                send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title=pro_name, text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)

            return 31500
        return wrapper
    return try_func


def async(func):
    """
    异步开线程调用
    :param func: 被修饰的函数
    :return:
    """
    def wrapper(*args, **kwargs):
        thr = Thread(target=func, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def elapse_time(func):
    """
    计算方法耗时
    :param func: 被修饰的函数
    :return:
    """
    def wrapper(*args, **kwargs):
        st = current_timestamp()
        res = func(*args, **kwargs)
        et = current_timestamp()
        log.info("%s ELAPSE TIME: %s" % (func.__name__, (et-st)/1000.0))
        return res
    return wrapper


def thread_save(func):
    @wraps(func)
    def processed_res(*args, **kwargs):
        save_mutex.acquire()
        st = time.time()
        res = func(*args, **kwargs)
        et = time.time()
        save_mutex.release()
        log.info(u"%s: DONE %s" % (func.__name__, (et-st)))
        return res
    return processed_res