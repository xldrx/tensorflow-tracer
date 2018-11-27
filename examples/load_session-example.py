#! /usr/bin/env python -u
# coding=utf-8
import time

from tftracer import TracingServer

__author__ = 'Sayed Hadi Hashemi'
if __name__ == '__main__':
    server = TracingServer()
    server.load_session("session.pickle")

    # TODO(xldrx): Slow Server Workaround
    time.sleep(5)

    server.join()
