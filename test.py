from plc import plc_snap7

plc = plc_snap7()
plc.connect("192.168.37.144")
print(plc.get_connected())
plc.get_bool("input",0.6)