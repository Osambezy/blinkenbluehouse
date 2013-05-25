import socket
import os
import sys
import threading
import Queue
from time import time

import config
import mcuf
import blthreads
import playlist
import webinterface


MCU_HOST = config.MCU_HOST
MCU_PORT = config.MCU_PORT
WIDTH = config.WIDTH
HEIGHT = config.HEIGHT
LISTEN_PORT = config.LISTEN_PORT
INTERACTIVE_TIMEOUT = config.INTERACTIVE_TIMEOUT
VU_TIMEOUT = config.VU_TIMEOUT
HTTP_PORT = config.HTTP_PORT
HTTP_ENABLE = config.HTTP_ENABLE
GAME_COLUMN = config.GAME_COLUMN
if GAME_COLUMN > WIDTH - 1:
    raise Exception('Error in config: GAME_COLUMN value too big')
scriptpath = os.path.abspath(os.path.dirname(sys.argv[0]))


class UDPListener(threading.Thread):

    def __init__(self, port, queue):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.queue = queue
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind(('', port))
        self.start()

    def run(self):
        while True:
            packet = self.listen_socket.recv(1024)
            self.queue.put(packet)


class SSCCC:

    def __init__(self):
        self.mcu_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mcu_socket.connect((MCU_HOST, MCU_PORT))
        self.packet_queue = Queue.Queue()
        self.playlist = playlist.Playlist(scriptpath, WIDTH, HEIGHT)
        self.listener = UDPListener(LISTEN_PORT, self.packet_queue)
        if HTTP_ENABLE:
            web = webinterface.Server(HTTP_PORT, self.packet_queue,
                                      self.playlist)
        self.toggled = WIDTH * HEIGHT * '\x00'
        self.vu_direction = True
        self.switchstatus('startup')

    def send(self, what):
        try:
            self.mcu_socket.send(what)
        except socket.error:
            pass

    def switchstatus(self, newstatus, param=''):
        if newstatus == 'startup':
            print 'SSCCC running'
            self.blinker = blthreads.EmptyThread(
                WIDTH, HEIGHT, self.mcu_socket)
            self.blinker.start()
        elif newstatus == 'off':
            self.blinker.stop()
            self.toggled = WIDTH * HEIGHT * '\x00'
            print 'Switched off'
            self.send(mcuf.packet_alloff(WIDTH, HEIGHT))
        elif newstatus == 'on':
            self.blinker.stop()
            self.toggled = WIDTH * HEIGHT * '\x01'
            print 'All on'
            self.send(mcuf.packet_allon(WIDTH, HEIGHT))
        elif newstatus == 'anim':
            self.blinker.stop()
            print 'Animation mode'
            self.blinker = blthreads.Animation(
                WIDTH, HEIGHT, self.mcu_socket, pl=self.playlist)
            self.blinker.start()
        elif newstatus == 'vu':
            self.blinker.stop()
            print 'VU mode'
        elif newstatus == 'lukas':
            self.blinker.stop()
            print 'Hau-den-Lukas mode'
            self.blinker = blthreads.Lukas(
                WIDTH, HEIGHT, self.mcu_socket, lukas_colum=GAME_COLUMN)
            self.blinker.start()
        elif newstatus == 'interactive':
            self.blinker.stop()
            print 'Interactive mode: ' + param
            if param == 'snake':
                self.blinker = blthreads.SnakeGame(
                    WIDTH, HEIGHT, self.mcu_socket)
            elif param == 'pong':
                self.blinker = blthreads.PongGame(
                    WIDTH, HEIGHT, self.mcu_socket, GAME_COLUMN)
            elif param == 'tetris':
                self.blinker = blthreads.TetrisGame(
                    WIDTH, HEIGHT, self.mcu_socket)
            elif param == 'maze':
                self.blinker = blthreads.MazeGame(
                    WIDTH, HEIGHT, self.mcu_socket)
            else:
                print 'unknown game'
                return
            self.blinker.start()
        elif newstatus == 'text':
            self.blinker.stop()
            print 'Text: ' + param
            self.blinker = blthreads.ScrollingText(
                WIDTH, HEIGHT, mcu_socket, text=param)
            self.blinker.start()
        else:
            raise Exception('Unknown status mode: ' + newstatus)
        self.status = newstatus

    def handle_packet(self, packet):
        if len(packet) >= 2 and packet[0:2] == 'OF':
            self.switchstatus('off')
        elif len(packet) >= 2 and packet[0:2] == 'ON':
            self.switchstatus('on')
        elif len(packet) >= 4 and packet[0:2] == 'TG':
            if self.status == 'startup':
                self.status = 'off'
            if not (self.status == 'off' or self.status == 'on'):
                return
            try:
                n = int(packet[2:4])
            except ValueError:
                return
            if n < 0 or n >= WIDTH * HEIGHT:
                return
            if self.toggled[n] == '\x00':
                self.toggled = self.toggled[:n] + '\x01' + self.toggled[n + 1:]
            else:
                self.toggled = self.toggled[:n] + '\x00' + self.toggled[n + 1:]
            self.send(mcuf.packet_bool(self.toggled, WIDTH, HEIGHT))
        elif len(packet) >= 2 and packet[0:2] == 'AN':
            self.switchstatus('anim')
        elif len(packet) >= 2 and packet[0:2] == 'VU':
            self.switchstatus('vu')
            self.vu_direction = True
        elif len(packet) >= 2 and packet[0:2] == 'UV':
            self.switchstatus('vu')
            self.vu_direction = False
        elif len(packet) > 2 and packet[0:2] == 'IN':
            self.switchstatus('interactive', param=packet[2:])
        elif len(packet) >= 3 and packet[0:2] == 'ID':
            if self.status == 'interactive':
                self.blinker.keypress(packet[2:])
        elif len(packet) > 2 and packet[0:2] == 'TX':
            self.switchstatus('text', param=packet[2:])
        elif len(packet) >= 2 and packet[0:2] == 'HB':
            self.in_timeout_time = time()
        elif len(packet) >= 3 and packet[0:2] == 'VD':
            if self.status == 'startup' or self.status == 'anim':
                self.switchstatus('vu')
            if self.status != 'vu':
                return
            data = WIDTH * HEIGHT * '\x00'
            vol = ord(packet[2])
            if vol > HEIGHT:
                vol = HEIGHT
            for i in range(vol):
                if self.vu_direction:
                    data = data[:(HEIGHT - 1 - i) * WIDTH] + '\x01' + \
                        data[(HEIGHT - 1 - i) * WIDTH + 1:]
                else:
                    data = data[:i * WIDTH] + '\x01' + data[i * WIDTH + 1:]
            if len(packet) > 3:
                vol2 = ord(packet[3])
                if vol2 > HEIGHT:
                    vol2 = HEIGHT
                for i in range(vol2):
                    if self.vu_direction:
                        data = data[:(HEIGHT - 1 - i) * WIDTH + 1] + '\x01' + \
                            data[(HEIGHT - 1 - i) * WIDTH + 2:]
                    else:
                        data = data[:i * WIDTH + 1] + '\x01' + \
                            data[i * WIDTH + 2:]
            self.send(mcuf.packet_bool(data, WIDTH, HEIGHT))
            self.vu_timeout_time = time()
        elif len(packet) >= 3 and packet[0:2] == 'LU':
            if not self.status == 'lukas':
                self.switchstatus('lukas')
            value = float(packet[2:])
            if value == 0:
                self.blinker.reset()
            else:
                self.blinker.hau(value)

    def mainloop(self):
        self.in_timeout_time = time()
        self.vu_timeout_time = time()
        while True:
            try:
                packet = self.packet_queue.get(True, 1.0)
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                break
            else:
                self.handle_packet(packet)
            if self.status == 'interactive' and \
                    time() > self.in_timeout_time + INTERACTIVE_TIMEOUT:
                print 'Interactive timeout! Switching to animation mode.'
                self.switchstatus('anim')
            elif self.status == 'vu' and \
                    time() > self.vu_timeout_time + VU_TIMEOUT:
                print 'VU timeout! Switching to animation mode.'
                self.switchstatus('anim')
        self.mcu_socket.close()


if __name__ == '__main__':
    ssccc = SSCCC()
    ssccc.mainloop()
