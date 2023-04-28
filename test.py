import time
current_time = time.time()
from plc import plc_snap7
plc = plc_snap7()
plc.connect("192.168.36.5")

plc.get_floats("db",276,6,2)
print(time.time()-current_time)

current_time = time.time()
plc.get_chars("db",300,6,2)
print(time.time()-current_time)
time.sleep(10)