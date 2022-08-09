from plc import plc_snap7
import time
from multiprocessing import Process, Pipe

pipe_main, pipe_sub = Pipe(True)

def get_running_time(func):
    start_time = time.time()
    def fun(*args, **kwargs):
        res = func(*args, **kwargs)
        print(time.time() - start_time)
        return res
    return fun
class test(object):

    #@get_running_time
    def a(self,pipe_sub, x):
        while True:
            print(111)
            cmd = pipe_sub.recv()
            if cmd=="1":
                for i in range(x):
                    print(i)
            if cmd=="2":
                print("ok")

    def run(self):
        rafcon_process = Process(target=self.a, args=(pipe_sub,1000,))
        rafcon_process.start()

# if __name__ == '__main__':
#     aa = test()
#     aa.run()
#     pipe_main.send("2")

