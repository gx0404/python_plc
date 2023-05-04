import time
current_time = time.time()
from plc import plc_snap7
plc = plc_snap7()
plc.connect("192.168.36.5")

print(plc.set_char("db",302,"a",2))