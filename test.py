from plc import plc_snap7

plc = plc_snap7()
plc.connect("192.168.37.5")
import time
current_time = time.time()
print(plc.get_char("db",300,6,2))