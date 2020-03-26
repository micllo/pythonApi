# -*- coding:utf-8 -*-
import xlrd, os


def read_excel(filename, index):
    """
    读取excel操作，所有数据存放在字典中
    :param filename: Excel文件
    :param index: 工作表索引
    :return:
    """
    xls = xlrd.open_workbook(filename)
    sheet = xls.sheet_by_index(index)
    # print(sheet.nrows)
    # print(sheet.ncols)
    excel_list = []
    for row_index in range(sheet.nrows):
        if row_index > 0:
            line_dict = {}
            for col_index in range(sheet.ncols):
                line_dict[sheet.row_values(0)[col_index]] = sheet.row_values(row_index)[col_index]
            excel_list.append(line_dict)
    return excel_list


if __name__ == '__main__':
    current_path = os.path.split(os.path.realpath(__file__))[0].split('Tools')[0]
    print(current_path)
    excel_list = read_excel(current_path + "api_case_tmpl.xlsx", 0)
    for line_dict in excel_list:
        print(line_dict)

