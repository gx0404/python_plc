import time
from plc import plc_snap7
import random
current_time = time.time()
plc = plc_snap7()
plc.connect("192.168.37.144")
print(f"connect time is {time.time()-current_time}")
while 1:
    int_value_list = []
    for i in range(1202,2202,2):
        value = random.randint(-32768,32767)
        plc.set_int("db",i,value,2)
        int_value_list.append(value)
    print(f"set data time is {time.time() - current_time}")
    current_time = time.time()
    check_value_list = plc.get_ints("db",1202,500,2)

    if check_value_list!=int_value_list:
        print(int_value_list)
        print(check_value_list)
        raise "fault"
    print(f"read data time is {time.time() - current_time}")
    current_time = time.time()
