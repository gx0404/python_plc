import json
import os

path = os.path.dirname(__file__)


class ReadWriteJson(object):
    def __init__(self):
        file1_name = "value.json"
        file2_name = "config.json"
        self.path1 = os.path.join(path, file1_name)
        self.path2 = os.path.join(path, file2_name)
        with open(self.path1) as value_json:
            # self.value_list_old = json.load(value_json)
            self.value_list_old = {
                "operation": "set_bool output goble values 0.2",
                "plc_address": "192.168.36.5",
                "value": False,
                "value_type": "output goble values"
            }
        with open(self.path2) as config_json:
            # self.config_list_old = json.load(config_json)
            self.config_list_old = {"io_type_dict": {"input": 129, "mw": 131, "m_bool": 131, "db": 132, "output": 130}}

    def read(self, name):
        if name in tuple(self.value_list_old):
            return self.value_list_old[name]
        elif name in tuple(self.config_list_old):
            return self.config_list_old[name]
        else:
            raise Exception("load json error")

    def write(self, value_type, value):
        value_list_new = self.value_list_old
        if value_type in self.value_list_old.keys():
            try:
                with open(self.path1, "w") as value_json:
                    value_list_new[value_type] = value
                    json.dump(value_list_new, value_json, indent=4, sort_keys=True)
            except Exception as error:
                print(error)
                with open(self.path1, "w") as value_json:
                    json.dump(self.value_list_old, value_json, indent=4, sort_keys=True)
        else:
            raise Exception("write json error")
