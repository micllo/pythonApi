# -*- coding: utf-8 -*-
"""
时间日期的转化文件
"""
import time
import datetime
from datetime import timedelta


def get_date_by_days(days=1, time_type="%Y-%m-%dT H:%M:%S"):
    """
    获取 多少天 之前 的日期
    :param days:
    :param time_type:
    :return:
    """
    # 格式化为 年 月 日
    # return (datetime.date.today() - timedelta(days=days)).strftime(time_type)
    # 格式化为 年 月 日 时 分 秒
    return (datetime.datetime.now() - timedelta(days=days)).strftime(time_type)


# @return: 当前的datetime时间戳
def now_dt():
    return datetime.datetime.now()


# 当前时间
def current_date():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def current_day():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def current_mth():
    return datetime.datetime.now().strftime('%Y-%m')


def current_timestamp():
    current_timestamp_var = int(time.time()*1000)

    return current_timestamp_var


# @return: 当前的date
def now_date():
    return datetime.datetime.now().date()


# @return: 返回1970.01.01，datetime类型
def null_dt():
    return datetime.datetime(1970, 1, 1)


# @return: 返回1970.01.01，date类型
def null_date():
    return datetime.date(1970, 1, 1)


# @param: 输入日期格式，
# @return: datetime类型
def get_dt(dt_str="1970-01-01 00:00:00", dt_format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.strptime(dt_str, dt_format)


# @param: 输入日期格式，
# @return: date类型
def get_date(date_str="1970-01-01", dt_format='%Y-%m-%d'):
    return get_dt(date_str, dt_format).date()


def get_dt_day(dt, dt_format='%Y-%m-%d'):
    return dt.strftime(dt_format)


# @param: datetime
# @return: string类型
def get_dt_mth(dt, dt_format='%Y-%m'):
    return dt.strftime(dt_format)


# @param: datetime
# @return: string类型
def get_dt_str(dt, dt_format="%Y-%m-%d %H:%M:%S"):
    return dt.strftime(dt_format)


def timestamp_tran_date_str(timestamp):
    """
    时间戳转化成字符型日期格式
    :return: 字符型日期格式
    """
    return time.strftime('%Y-%m-%d', time.localtime(timestamp/1000))


def date_str_tran(date_str):
    """
    将字符串格式时间转成 timestamp 13位格式
    :param date_str: 需要转换的时间
    :return: datetime
    """
    try:
        date_tuple = time.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        timestamp = int(time.mktime(date_tuple)*1000)
    except Exception as e:
        print(e)
        timestamp = None
    return timestamp


def timestamp_str_tran(timestamp):
    """
    将字符串格式的时间戳 转成 日期格式
    :param timestamp:
    :return:
    """
    if timestamp:
        try:
            time_array = time.localtime(int(timestamp) / 1000)
            date = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
        except Exception as e:
            print(e)
    else:
        date = "None"
    return date


if __name__ == "__main__":
    # print date_time_to_sec("2015-01-01 10:20:20")
    # print date_to_sec("2015-01-01")
    # print mth_time_to_sec("2015-01")
    # print time_to_sec("10:20:20")
    # print mth_between("2014-12", "2015-02")
    # print find_span_trans_date([])
    # print validate_time_format("2015-01-01 10")
    # print mth_used("", "")
    # print current_week_days(return_type="tsp")
    # print date_num_str_tra_timestamp("20160214")
    import tushare as ts
    print(ts.get_hist_data("600759"))
