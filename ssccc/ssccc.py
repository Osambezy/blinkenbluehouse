import mcuf
import blthreads
import playlist
import webinterface

import time, socket, os, sys
import threading
import Queue

import config
MCU_HOST = config.MCU_HOST
MCU_PORT = config.MCU_PORT
WIDTH = config.WIDTH
HEIGHT = config.HEIGHT
LISTEN_PORT = config.LISTEN_PORT
INTERACTIVE_TIMEOUT = config.INTERACTIVE_TIMEOUT
HTTP_PORT = config.HTTP_PORT
HTTP_ENABLE = config.HTTP_ENABLE
GAME_COLUMN = config.GAME_COLUMN

if GAME_COLUMN > WIDTH - 1: raise Exception, "Error in config: GAME_COLUMN value too big"

scriptpath = os.path.abspath(os.path.dirname(sys.argv[0]))

mcu_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mcu_socket.connect((MCU_HOST, MCU_PORT))

def send(what):
  try:
    mcu_socket.send(what)
  except socket.error:
    pass

class UDPListener(threading.Thread):
  def __init__(self, port, queue):
    threading.Thread.__init__(self)
    self.setDaemon(True)
    self.queue = queue
    self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.listen_socket.bind(('', port))
    #self.listen_socket.settimeout(1)
    self.start()

  def run(self):
    while True:
      packet = self.listen_socket.recv(1024)
      self.queue.put(packet)

packet_queue = Queue.Queue()
playlist = playlist.Playlist(scriptpath, WIDTH, HEIGHT)
listener = UDPListener(LISTEN_PORT, packet_queue)

if HTTP_ENABLE:
  web = webinterface.Server(HTTP_PORT, packet_queue, playlist)

blinker = blthreads.BlinkerThread(WIDTH, HEIGHT, mcu_socket)
blinker.start() # leerer Thread, macht vorerst gar nix

status = ""
toggled = WIDTH*HEIGHT*"\x00"
vu_direction = True

def switchstatus(newstatus, param=""):
  global status, toggled, mcu_socket, blinker
  if newstatus == "startup":
    print "SSCCC running"
  elif newstatus == "off":
    blinker.stop()
    toggled = WIDTH*HEIGHT*"\x00"
    print "Switched off"
    send(mcuf.packet_alloff(WIDTH,HEIGHT))
  elif newstatus == "on":
    blinker.stop()
    toggled = WIDTH*HEIGHT*"\x01"
    print "All on"
    send(mcuf.packet_allon(WIDTH,HEIGHT))
  elif newstatus == "anim":
    blinker.stop()
    print "Animation mode"
    blinker = blthreads.Animation(WIDTH, HEIGHT, mcu_socket, pl=playlist)
    blinker.start()
  elif newstatus == "vu":
    blinker.stop()
    print "VU mode"
  elif newstatus == "lukas":
    blinker.stop()
    print "Hau-den-Lukas mode"
    blinker = blthreads.Lukas(WIDTH, HEIGHT, mcu_socket, col=GAME_COLUMN)
    blinker.start()
  elif newstatus == "interactive":
    blinker.stop()
    print "Interactive mode: " + param
    blinker = blthreads.Game(WIDTH, HEIGHT, mcu_socket, game=param, col=GAME_COLUMN)
    blinker.start()
  elif newstatus == "text":
    blinker.stop()
    print "Text: " + param
    blinker = blthreads.Lauftext(WIDTH, HEIGHT, mcu_socket, text=param)
    blinker.start()
  else: raise Exception, "Internal error: unknown status mode: " + newstatus
  status = newstatus

switchstatus("startup")

to_time = time.time()
vol = 0
while True:
  try:
    packet = packet_queue.get(True, 1.0)
    if len(packet)>=2 and packet[0:2] == "OF":
      switchstatus("off")
    elif len(packet)>=2 and packet[0:2] == "ON":
      switchstatus("on")
    elif len(packet)>=4 and packet[0:2] == "TG":
      if status=="startup": status = "off"
      if status=="off" or status=="on":
        try: n = int(packet[2:4])
        except ValueError: pass
        else:
          if n>=0 and n<WIDTH*HEIGHT:
            if toggled[n]=="\x00": toggled = toggled[:n] + "\x01" + toggled[n+1:]
            else: toggled = toggled[:n] + "\x00" + toggled[n+1:]
            send(mcuf.packet_bool(toggled,WIDTH,HEIGHT))
    elif len(packet)>=2 and packet[0:2] == "AN":
      switchstatus("anim")
    elif len(packet)>=2 and packet[0:2] == "VU":
      switchstatus("vu")
      vu_direction = True
    elif len(packet)>=2 and packet[0:2] == "UV":
      switchstatus("vu")
      vu_direction = False
    elif len(packet)>2 and packet[0:2] == "IN":
      switchstatus("interactive", param=packet[2:])
    elif len(packet)>2 and packet[0:2] == "TX":
      switchstatus("text", param=packet[2:])
    elif len(packet)>=2 and packet[0:2] == "HB":
      to_time = time.time()
    elif len(packet)>=3 and packet[0:2] == "VD":
      if status=="startup": switchstatus("vu")
      if status=="vu":
        data = WIDTH * HEIGHT * '\x00'
        vol = ord(packet[2])
        if vol > HEIGHT: vol = HEIGHT
        for i in range(vol):
          if vu_direction: data = data[:(HEIGHT-1-i)*WIDTH] + '\x01' + data[(HEIGHT-1-i)*WIDTH+1:]
          else: data = data[:i*WIDTH] + '\x01' + data[i*WIDTH+1:]
        if len(packet)>3:
          vol2 = ord(packet[3])
          if vol2 > HEIGHT: vol2 = HEIGHT
          for i in range(vol2):
            if vu_direction: data = data[:(HEIGHT-1-i)*WIDTH+1] + '\x01' + data[(HEIGHT-1-i)*WIDTH+2:]
            else: data = data[:i*WIDTH+1] + '\x01' + data[i*WIDTH+2:]
        send(mcuf.packet_bool(data,WIDTH,HEIGHT))
    elif len(packet)>=3 and packet[0:2] == "ID":
      if status=="interactive": blinker.keypress(packet[2:])
    elif len(packet)>=3 and packet[0:2] == "LU":
      if not status=="lukas": switchstatus("lukas")
      value = float(packet[2:])
      if value == 0:
        blinker.reset()
      else:
        blinker.hau(value)
  except Queue.Empty: pass
  except KeyboardInterrupt: break
  if status == "interactive" and time.time() > to_time + INTERACTIVE_TIMEOUT:
    print "Interactive timeout! Switching to animation mode."
    switchstatus("anim")

mcu_socket.close()

