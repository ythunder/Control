# coding=utf-8
import socket
import select
import sys
import threading
import time
import logging
import os

logsDir = "logs"
if not os.path.isdir(logsDir):
    os.mkdir(logsDir)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='logs/logs.log',
                    filemode='a')


maxConnetions = 32


class Proxy:
    def __init__(self, addr):
        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy.bind(addr)
        self.proxy.listen(maxConnetions)
        self.inputs = {self.proxy: None}
        self.route = {}

    def serve_forever(self, to_addr):
        logging.info('proxy listen...')
        while 1:
            readable, _, _ = select.select(list(self.inputs.keys()), [], [])
            for self.sock in readable:
                if self.sock == self.proxy:
                    self.on_join(to_addr)
                else:
                    try:
                        data = self.sock.recv(8192)
                    except Exception, e:
                        logging.error(str(e))
                        self.on_quit()
                        continue

                    if not data:
                        self.on_quit()
                    else:
                        try:
                            self.route[self.sock].send(data)
                        except Exception, e:
                            logging.error(str(e))
                            self.on_quit()
                            continue

    def on_join(self, to_addr):
        client, addr = self.proxy.accept()
        logging.info("proxy client " + str(addr) + 'connect')
        forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            forward.connect(to_addr)
        except Exception, e:
            logging.error(str(e))
            client.close()
            return
        self.inputs[client] = None
        self.inputs[forward] = None

        self.route[client] = forward
        self.route[forward] = client

        # 删除连接

    def on_quit(self):
        ls = [self.sock]
        if self.sock in self.route:
            ls.append(self.route[self.sock])
        for s in ls:
            if s in self.inputs:
                del self.inputs[s]
            if s in self.route:
                del self.route[s]
            s.close()


# if __name__ == "__main__":
#
#     # C的IP和端口
#     to_addr = ('127.0.0.1', 8899)
#
#     try:
#         proxy = Proxy(('', 9999))
#         proxy.serve_forever(to_addr)
#     except KeyboardInterrupt, e:
#         logging.error("KeyboardInterrupt" + str(e))