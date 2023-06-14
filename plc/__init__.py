# -*- coding: utf-8 -*-
import time

import snap7
import os
import struct
import math
import sys

path = os.path.dirname(__file__)
sys.path.append(path)

from config.read_write import ReadWriteJson
from config import io_type_dict
"""从plc读取的byte转换为int"""


def plc_byte_num(data):
    num = 0
    for i in range(len(data)):
        if int(data[len(data) - 1 - i]) == 1:
            num += pow(2, i)
    return num


"""带符号int转化为2进制"""
"""plc一个int两个2进制byte，plc读取顺序从右往左"""


def num_plc_byte(data, byte_num):
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
        self.read_write = ReadWriteJson()
        # 从config.json拿去读取类型，和从config.json里读取plc地址，防止重复连接
        # self.io_type_dict = self.read_write.read("io_type_dict")
        self.io_type_dict = io_type_dict
        self.ip = self.read_write.read("plc_address")
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
            self.read_write.write("plc_address", ip)
            try:
                self.plc.connect(ip, 0, 1)
                return self.plc.get_connected()
            except Exception as error:
                print(error)
                return False
    """判断snap7与plc连接状态"""

    def get_connected(self):
        return self.plc.get_connected()

    def dis_connected(self):
        return self.plc.disconnect()

    """读取bool值，返回值为读取的byte，和右移到最后一位的值（用于判断所要的bool值）"""

    def read_bool(self, read_type, address, db_address=0):
        byte_address = int(address)
        io_address = int(round((address - byte_address) * 10))
        # 从plc拿取所需要的bool值整个byte为data,下面是判断是否为db块的bool
        data = self.plc.read_area(self.io_type_dict[read_type], db_address, byte_address, 1)
        data = struct.unpack('!B', data)
        data = data[0]
        # data1为右移byte后所得的值，用于判断bool
        data1 = data >> io_address
        return data, data1

    """对读写value.json的read_write重复步骤"""

    def write_json(self, name, write_type, address, status, db_address=0):
        if db_address == 0:
            db_write = "goble_values"
        else:
            db_write = f"db{db_address}"
        self.read_write.write("operation", "{} {} {} {}".format(name, write_type, db_write, address))
        self.read_write.write("value_type", write_type + " {}".format(db_write))
        self.read_write.write("value", status)

    """读取plc input、output、m_bool、DB块的bool值,
    args为io_type:{input,output,m_bool，DB},address:{plc bool 地址,db_address:{db的地址}}"""

    def get_bool(self, io_type, address, db_address=0):
        byte_data, bool_data = self.read_bool(io_type, address, db_address)
        # 判断移位后的bool_data bool值
        if bool_data % 2 == 0:
            io_status = False
        else:
            io_status = True
        self.write_json(self.get_bool.__name__, io_type, address, io_status, db_address)
        return io_status

    """bool 赋值，args为io_type:{input,output,m_bool，DB},value:{bool值},address:{plc bool 地址,db_address:{db的地址}}"""

    def set_bool(self, io_type, address, value, db_address=0):
        # 赋值bool需要先拿到bool所在的byte值，避免直接影响同byte下的bool
        byte_data, bool_data = self.read_bool(io_type, address, db_address)
        # 判断移位后的bool_data bool值
        if bool_data % 2 == 0:
            io_status = False
            # 判断赋值是否与实际值一致
            if io_status == value:
                pass
            else:
                # int(round(math.modf(address)[0] * 10))为bool在byte里实际位置
                # 需要更改bool时，是byte里单独一个bit需要修改
                out = byte_data + 2 ** int(round(math.modf(address)[0] * 10))
                out = struct.pack('!B', out)
                self.plc.write_area(self.io_type_dict[io_type], db_address, int(address), out)
        else:
            io_status = True
            # 判断赋值是否与实际值一致
            if io_status == value:
                pass
            else:
                # int(round(math.modf(address)[0] * 10))为bool在byte里实际位置
                # 需要更改bool时，是byte里单独一个bit需要修改
                out = byte_data - 2 ** int(round(math.modf(address)[0] * 10))
                out = struct.pack('!B', out)
                self.plc.write_area(self.io_type_dict[io_type], db_address, int(address), out)
        self.write_json(self.set_bool.__name__, io_type, address, io_status, db_address)
        return True

    """读取 setting DB块 INT值"""

    def get_ints(self, io_type, int_address, array_num, db_address=0):
        data = self.plc.read_area(self.io_type_dict[io_type], db_address, int_address, 2*array_num)
        # # 读取plc的两个byte转换为二进制
        # plc_byte1 = "{:b}".format(data[0])
        # plc_byte2 = "{:b}".format(data[1])
        res_list = []
        for i in range(0,len(data),2):
            int_bytes = data[i:i+2]
            int_value = int.from_bytes(int_bytes,"big")
            if int_value < 32768:
                res = int_value
            else:
                res = -(65536 - int_value)
            res_list.append(res)
        # # 未考虑负数直接得到两个byte的整数值
        # num1 = (plc_byte_num(plc_byte1)) << 8
        # num2 = plc_byte_num(plc_byte2)
        # num = num1 + num2
        # # 判断int值是否为负数
        # if num < 32768:
        #     res = num
        # else:
        #     res = -(65536 - num)
        self.write_json(self.get_ints.__name__, io_type, int_address, res, db_address)
        return res_list

    """赋值plc DB块 INT值"""
    "int值为正数时，第一个字节的最高位为0，负数则为1"

    def set_int(self, io_type, int_address, value, db_address=0):
        if value > 32767 or value < -32769:
            print("请输入有效的int值，范围在32766--32768之间")
            raise Exception("无效的int值")
        # 从num_plc_byte转化为两个2进制
        byte_list = num_plc_byte(value, 2)
        # 两个二进制转为int打包
        data1 = struct.pack("!B", int(byte_list[1], 2))
        data2 = struct.pack("!B", int(byte_list[0], 2))
        self.plc.write_area(self.io_type_dict[io_type], db_address, int_address, data1)
        self.plc.write_area(self.io_type_dict[io_type], db_address, int_address + 1, data2)
        self.write_json(self.set_int.__name__, io_type, int_address, value, db_address)
        return True

    def get_floats(self, io_type, float_address, array_num, db_address=0):
        float_res_list = []
        for i in range(array_num):
            data = self.plc.read_area(self.io_type_dict[io_type], db_address, float_address + i * 4, 4)
            float_res = struct.unpack('!f', data)
            float_res_list.append(float_res[0])
        return float_res_list

    def set_float(self, io_type, float_address, value, db_address=0):
        real_value = struct.pack('!f', value)
        self.plc.write_area(self.io_type_dict[io_type], db_address, float_address, real_value)
        return True

    def get_chars(self, io_type, char_address, array_num, db_address=0):
        char_res_list = ""
        for i in range(array_num):
            data = self.plc.read_area(self.io_type_dict[io_type], db_address, char_address + i * 1, 1)
            char_result = data.decode("utf-8", errors="ignore")
            char_res_list = char_res_list + char_result
        return char_res_list

    def set_char(self, io_type, char_address, value, db_address=0):
        if not isinstance(value, str):
            raise Exception("无效的字符串")
        else:
            if len(value) > 1:
                raise Exception("字符只能为一个单位")
            if len(value) == 0:
                value = " "
            char_value = value.encode("utf-8")
            self.plc.write_area(self.io_type_dict[io_type], db_address, char_address, char_value)
            return True
