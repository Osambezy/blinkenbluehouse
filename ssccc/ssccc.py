import mcuf
import blthreads
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

mcu_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mcu_socket.connect((MCU_HOST, MCU_PORT))

def send(what):
  try:
    mcu_socket.send(what)
  except socket.error:
    pass

class UDPListener(threading.Thread):
  def __init__(self, queue, port):
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

scriptpath = os.path.abspath(os.path.dirname(sys.argv[0]))
animpath = scriptpath + "/animations/" + str(WIDTH) + "x" + str(HEIGHT) + "/"
try:
  anims = os.listdir(animpath)
  playlist = [animpath+"/"+anim for anim in anims]
except OSError:
  print "No animations available for " + str(WIDTH) + "x" + str(HEIGHT)
  playlist = []
#TODO: save, load and modify playlist on-the-fly via webinterface, telnet, etc.

packet_queue = Queue.Queue()
listener = UDPListener(packet_queue, LISTEN_PORT)

if HTTP_ENABLE:
  web = webinterface.Server(packet_queue, HTTP_PORT)

blinker = blthreads.BlinkerThread(WIDTH, HEIGHT, mcu_socket)
blinker.start() # leerer Thread, macht vorerst gar nix

status = ""
toggled = WIDTH*HEIGHT*"\x00"

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
    blinker = blthreads.Animation(WIDTH, HEIGHT, mcu_socket)
    blinker.playlist = playlist
    blinker.start()
  elif newstatus == "vu":
    blinker.stop()
    print "VU mode"
  elif newstatus == "lukas":
    blinker.stop()
    print "Hau-den-Lukas mode"
    blinker = blthreads.Lukas(WIDTH, HEIGHT, mcu_socket)
    blinker.start()
  elif newstatus == "interactive":
    blinker.stop()
    print "Interactive mode: " + param
    blinker = blthreads.Game(WIDTH, HEIGHT, mcu_socket, game=param)
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
heartbeat = False
vol = 0
while True:
  try:
    packet = packet_queue.get(True, INTERACTIVE_TIMEOUT)
    if len(packet)>=2 and packet[0:2] == "OF":
      switchstatus("off")
    elif len(packet)>=2 and packet[0:2] == "ON":
      switchstatus("on")
    elif len(packet)>=3 and packet[0:2] == "TG":
      if status=="off" or status=="on":
        if toggled[ord(packet[2])]=="\x00": toggled = toggled[:ord(packet[2])] + "\x01" + toggled[ord(packet[2])+1:]
        else: toggled = toggled[:ord(packet[2])] + "\x00" + toggled[ord(packet[2])+1:]
        send(mcuf.packet_bool(toggled,WIDTH,HEIGHT))
    elif len(packet)>=2 and packet[0:2] == "AN":
      switchstatus("anim")
    elif len(packet)>=2 and packet[0:2] == "VU":
      switchstatus("vu")
    elif len(packet)>2 and packet[0:2] == "IN":
      switchstatus("interactive", param=packet[2:])
    elif len(packet)>2 and packet[0:2] == "TX":
      switchstatus("text", param=packet[2:])
    elif len(packet)>=2 and packet[0:2] == "HB":
      heartbeat = True
    elif len(packet)>=3 and packet[0:2] == "VD":
      if status=="startup": switchstatus("vu")
      if status=="vu":
        vol = ord(packet[2])
        if vol > HEIGHT: vol = HEIGHT
        if len(packet)>3:
          vol2 = ord(packet[3])
          if vol2 > HEIGHT: vol2 = HEIGHT
        #send(mcuf.packet_bool((WIDTH*HEIGHT-vol)*"\x00"+vol*"\x01",WIDTH,HEIGHT))
        data = WIDTH * HEIGHT * '\x00'
        for i in range(vol):
          data = data[:(HEIGHT-i)*WIDTH-2] + '\x01' + data[(HEIGHT-i)*WIDTH-1:]
        for i in range(vol2):
          data = data[:(HEIGHT-i)*WIDTH-1] + '\x01' + data[(HEIGHT-i)*WIDTH:]
        send(mcuf.packet_bool(data,WIDTH,HEIGHT))
    elif len(packet)>=2 and packet[0:2] == "V+":
      if status=="vu":
        try: vol = (vol + 1) % (WIDTH*HEIGHT)
        except socket.error: pass
        if vol > WIDTH * HEIGHT: vol = WIDTH * HEIGHT
        send(mcuf.packet_bool((WIDTH*HEIGHT-vol-1)*"\x00"+"\x01"+(vol)*"\x00",WIDTH,HEIGHT))
    elif len(packet)>=3 and packet[0:2] == "ID":
      if status=="interactive": blinker.keypress(packet[2:])
    elif len(packet)>=3 and packet[0:2] == "LU":
      if not status=="lukas": switchstatus("lukas")
      value = float(packet[2:])
      if value == 0:
        blinker.reset()
      else:
        blinker.hau(value)
  except Queue.Empty:
    if heartbeat: heartbeat = False
    else:
      if status == "interactive":
        print "Timeout!"
        switchstatus("anim")
  except KeyboardInterrupt:
    break

mcu_socket.close()

