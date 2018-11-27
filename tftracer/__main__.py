#! /usr/bin/env python -u
# coding=utf-8
__author__ = 'Sayed Hadi Hashemi'

import argparse
import errno
import os
import time
import traceback
from . import TracingServer

FLAGS = None


def arg_parser():
    global FLAGS
    parser = argparse.ArgumentParser("tftracer")
    parser.add_argument(
        "--port",
        type=int,
        help="To what TCP port web server to listen",
        default="9999"
    )
    parser.add_argument(
        "--ip",
        type=str,
        help="To what IP address web server to listen",
        default="0.0.0.0"
    )
    parser.add_argument(
        "session_file",
        type=str,
        help="Path to the trace session file"
    )
    FLAGS, _ = parser.parse_known_args()

def main():

    arg_parser()

    filename = FLAGS.session_file
    if not os.path.exists(filename):
        print("File not found: {}".format(filename))
        exit(errno.ENOENT)
    else:
        server = TracingServer(server_port=FLAGS.port, server_ip=FLAGS.ip)
        try:
            server.load_session(filename)
            # todo(xldrx): workaround
            time.sleep(5)
            server.join()
        except Exception as ex:
            traceback.print_exc()
            print(ex)
            server.stop_web_server()
            exit()


if __name__ == '__main__':
    main()
