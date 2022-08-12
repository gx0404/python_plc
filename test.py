from plc import plc_snap7

plc = plc_snap7()
plc.connect("10.3.7.21")
print(plc.get_connected())
print(plc.get_bool("input",0.4))