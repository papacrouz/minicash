#!/usr/bin/env python

import threading
import context 
import time


ThreadMapper = {0: "Minting thread", 1: "Client thread", 2: "Server thread"}

shutdownLock = threading.Lock()



def shutdown():
    with shutdownLock:
        if context.fShutdown:
            return

        context.fShutdown = True


def check_for_shutdown(t):
    # handle shutdown 
    n = t.n
    if context.fShutdown:
        if n != -1:
            context.listfThreadRunning[n] = False
            t.exit = True
            print("Exiting {}".format(ThreadMapper[n]))



class ExitedThread(threading.Thread):
    def __init__(self, arg, n):
        super(ExitedThread, self).__init__()
        self.exit = False
        self.arg = arg
        self.n = n


    def run(self):
        self.thread_handler(self.arg, self.n)
        pass


    def thread_handler(self, arg, n):
        while True:
            check_for_shutdown(self)
            if self.exit:
                break
            context.listfThreadRunning[n] = True
            try:
                self.thread_handler2(arg)
            except Exception as e:
                print("ThreadHandler()")
                print(e)
            context.listfThreadRunning[n] = False

            time.sleep(5)
            pass


    def thread_handler2(self, arg):
        raise NotImplementedError("must impl this func")

        
    def check_self_shutdown(self):
        check_for_shutdown(self)


    def try_exit(self):
        self.exit = True
        context.listfThreadRunning[self.n] = False
        pass