import socket

import bus


class UDP2RS485(bus.Bus):

    def __init__(self, ip, port):
        self.myport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.myport.connect((ip, port))

    def __del__(self):
        self.myport.close()

    def send(self, data):
        self.myport.send(data)
