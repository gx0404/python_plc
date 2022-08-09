# -*- coding: utf-8 -*-
import snap7
import os
import struct
import math
import sys

path = os.path.dirname(__file__)
sys.path.append(path)
from config.read_write import Read_write_json

"""从plc读取的byte转换为int"""


def plcByte_num(data):
    num = 0
    for i in range(len(data)):
        if int(data[len(data) - 1 - i]) == 1:
            num += pow(2, i)
    return num


"""带符号word转化为2进制"""
"""plc一个word两个2进制byte，plc读取顺序从右往左"""


def num_plcByte(data, byte_num):
    byte_list = []
    if data >= 0:
        pass
    else:
        data = 65536 + data
    # 剔除bin函数生成“0b+转换为2进制的数”的0b
    byte = bin(data)[2:len(bin(data))]
    # bin函数生成的2进制需要补位到8个bit
    byte = "0" * (byte_num * 8 - len(byte)) + byte
    # 函数传入的数据全部拆分成byte，8个bit一组
    for i in range(1, byte_num + 1):
        byte_list.append(byte[(len(byte) - 8):len(byte)])
        byte = byte[0:(len(byte) - 8)]
    return byte_list


"""读写plc"""


class plc_snap7(object):
    def __init__(self):
        """从config.json读取配置,创建snap7"""
        self.read_write = Read_write_json()
        # 从config.json拿去读取类型，和从config.json里读取plc地址，防止重复连接
        self.io_type_dict = self.read_write.read("io_type_dict")
        self.ip = self.read_write.read("plc_adress")
        self.plc = snap7.client.Client()

    """连接plc，args为plc地址，plc_snap7实例化后只能连接一个plc"""
    """读取类型存放在config.json文件里，plc地址储存在value.json里"""

    def connect(self, ip):
        if self.plc.get_connected():
            if ip == self.ip:
                return True
            else:
                raise Exception("{} setting connected,you can't connect other setting".format(self.ip))
        else:
            self.read_write.write("plc_adress", ip)
            try:
                self.plc.connect(ip, 0, 1)
                return self.plc.get_connected()
            except Exception as error:
                print(error)
                return False

    """判断snap7与plc连接状态"""

    def get_connected(self):
        return self.plc.get_connected()

    """读取bool值，返回值为读取的byte，和右移到最后一位的值（用于判断所要的bool值）"""

    def read_bool(self, read_type, adress, db_adress=None):
        byte_adress = int(adress)
        io_adress = int(round((adress - byte_adress) * 10))
        # 从plc拿取所需要的bool值整个byte为data,下面是判断是否为db块的bool
        if db_adress is None:
            area_adress = 0
        else:
            area_adress = db_adress
        data = self.plc.read_area(self.io_type_dict[read_type], area_adress, byte_adress, 1)
        data = struct.unpack('!B', data)
        data = data[0]
        # data1为右移byte后所得的值，用于判断bool
        data1 = data >> io_adress
        return data, data1

    """对读写value.json的read_write重复步骤"""

    def write_json(self, name, write_type, adress, status, db_adress=None):
        self.read_write.write("operation", "{} {}{} {}".format(name, write_type, db_adress, adress))
        self.read_write.write("value_type", write_type + " {}".format(db_adress))
        self.read_write.write("value", status)

    """读取plc input、output、m_bool、DB块的bool值,
    args为io_type:{input,output,m_bool，DB},adress:{plc bool 地址,db_adress:{db的地址}}"""

    def get_bool(self, io_type, adress, db_adress=None):
        byte_data, bool_data = self.read_bool(io_type, adress, db_adress)
        # 判断移位后的bool_data bool值
        if bool_data % 2 == 0:
            io_status = False
        else:
            io_status = True
        self.write_json(self.get_bool.__name__, io_type, adress, io_status, db_adress)
        return io_status

    """bool 赋值，args为io_type:{input,output,m_bool，DB},value:{bool值},adress:{plc bool 地址,db_adress:{db的地址}}"""

    def set_bool(self, io_type, adress, value, db_adress=None):
        if db_adress is None:
            area_adress = 0
        else:
            area_adress = db_adress
        # 赋值bool需要先拿到bool所在的byte值，避免直接影响同byte下的bool
        byte_data, bool_data = self.read_bool(io_type, adress, db_adress)
        # 判断移位后的bool_data bool值
        if bool_data % 2 == 0:
            io_status = False
            # 判断赋值是否与实际值一致
            if io_status == value:
                pass
            else:
                # int(round(math.modf(adress)[0] * 10))为bool在byte里实际位置
                # 需要更改bool时，是byte里单独一个bit需要修改
                out = byte_data + 2 ** int(round(math.modf(adress)[0] * 10))
                out = struct.pack('!B', out)
                self.plc.write_area(self.io_type_dict[io_type], area_adress, int(adress), out)
        else:
            io_status = True
            # 判断赋值是否与实际值一致
            if io_status == value:
                pass
            else:
                # int(round(math.modf(adress)[0] * 10))为bool在byte里实际位置
                # 需要更改bool时，是byte里单独一个bit需要修改
                out = byte_data - 2 ** int(round(math.modf(adress)[0] * 10))
                out = struct.pack('!B', out)
                self.plc.write_area(self.io_type_dict[io_type], area_adress, int(adress), out)
        self.write_json(self.set_bool.__name__, io_type, adress, io_status, db_adress)
        return True

    """读取 setting DB块 WORD值"""

    def get_word(self, io_type, word_adress, db_adress=None):
        if db_adress is None:
            db_adress = 0
        data = self.plc.read_area(self.io_type_dict[io_type], db_adress, word_adress, 2)
        # 读取plc的两个byte转换为二进制
        plc_byte1 = "{:b}".format(data[0])
        plc_byte2 = "{:b}".format(data[1])
        # 未考虑负数直接得到两个byte的整数值
        num1 = (plcByte_num(plc_byte1)) << 8
        num2 = plcByte_num(plc_byte2)
        num = num1 + num2
        # 判断word值是否为负数
        if num < 32768:
            res = num
        else:
            res = -(65536 - num)
        self.write_json(self.get_word.__name__, io_type, word_adress, res, db_adress)
        return res

    """赋值plc DB块 WORD值"""
    "word值为正数时，第一个字节的最高位为0，负数则为1"

    def set_word(self, io_type, word_adress, value, db_adress=None):
        if db_adress is None:
            db_adress = 0
        if value > 32767 or value < -32769:
            print("请输入有效的word值，范围在32766--32768之间")
            raise Exception("无效的word值")
        # 从num_plcByte转化为两个2进制
        byte_list = num_plcByte(value, 2)
        # 两个二进制转为int打包
        data1 = struct.pack("!B", int(byte_list[1], 2))
        data2 = struct.pack("!B", int(byte_list[0], 2))
        self.plc.write_area(self.io_type_dict[io_type], db_adress, word_adress, data1)
        self.plc.write_area(self.io_type_dict[io_type], db_adress, word_adress + 1, data2)
        self.write_json(self.set_word.__name__, io_type, word_adress, value, db_adress)
        return True
