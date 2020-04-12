# -*- coding:utf-8 -*-
import xlrd, xlwt, os


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


def set_style(name, bold, colour, size):
    """
    [ 设置excel样式 ]
    :param name:    字体
    :param bold:    加粗
    :param colour:  颜色(索引)
    :param size:    大小(x20)
    :return:
    """
    style = xlwt.XFStyle()  # 初始化样式对象
    font = xlwt.Font()
    font.name = name
    font.bold = bold
    font.colour_index = colour
    font.height = size
    style.font = font
    al_style = xlwt.Alignment()  # 设置：水平居中、垂直居中
    al_style.horz = 0x02
    al_style.vert = 0x01
    style.alignment = al_style
    return style


def get_cell_data(file_name, table_index, row_num, col_num):
    """
    [ 获取某表的某单元格数据 ]
    :param file_name:
    :param table_index:
    :param row_num:
    :param col_num:
    :return:
    """
    data = xlrd.open_workbook(file_name)  # 打开xls文件、获取第x张表
    table = data.sheets()[table_index]
    return table.cell_value(row_num, col_num)


if __name__ == '__main__':
    current_path = os.path.split(os.path.realpath(__file__))[0].split('Tools')[0]
    print(current_path)
    excel_list = read_excel(current_path + "api_case_tmpl.xlsx", 0)
    for line_dict in excel_list:
        print(line_dict)

