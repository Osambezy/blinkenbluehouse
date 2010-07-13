import mcuf

import threading, sys, time, socket
import xml.dom.minidom

class BlinkerThread(threading.Thread):
  def __init__(self, width, height, mcu_socket):
    threading.Thread.__init__(self)
    self.setDaemon(True)
    self.control_event = threading.Event()
    self.control_value = 0
    self.mcu_socket = mcu_socket
    self.width = width
    self.height = height

  def run(self):
    # override in subclasses!
    pass

  def send(self, what):
    try: self.mcu_socket.send(mcuf.packet_bool(what, self.width, self.height))
    except socket.error: pass

  def clear(self):
    try: self.mcu_socket.send(mcuf.packet_alloff(self.width, self.height))
    except socket.error: pass

  def wait(self, waittime):
    while True:
      waitstart = time.time()
      self.control_event.wait(waittime)
      if self.control_event.isSet():
        self.control_event.clear()
        if self.control_value == 0: self.kill()
        else:
          waittime -= time.time() - waitstart
          if waittime<=0: return
      else:
        return

  def kill(self):
    try: self.mcu_socket.send(mcuf.packet_alloff(self.width, self.height))
    except: pass
    sys.exit()

  def stop(self):
    self.control_value = 0
    self.control_event.set()
    self.join()

class Game(BlinkerThread):
  def __init__(self, *args, **kwargs):
    BlinkerThread.__init__(self, *args)
    import game_tetris, game_snake, game_pong, game_maze
    if kwargs["game"] == "pong":
      self.main = game_pong.main
    elif kwargs["game"] == "tetris":
      self.main = game_tetris.main
    elif kwargs["game"] == "snake":
      self.main = game_snake.main
    elif kwargs["game"] == "maze":
      self.main = game_maze.main
    else:
      def x(self): print "unknown game"
      self.main = x
    self.controls = []

  def run(self):
    self.main(self)

  def keypress(self, keysym):
    if keysym in self.controls:
      self.control_value = self.controls.index(keysym) + 1
      self.control_event.set()

  def waitforkey(self, waittime, key):
    while True:
      waitstart = time.time()
      self.control_event.wait(waittime)
      if self.control_event.isSet():
        self.control_event.clear()
        if self.control_value == 0: self.kill()
        elif self.control_value == key: return True
        else:
          waittime -= time.time() - waitstart
          if waittime<=0: return False
      else:
        return False
  def waitforanykey(self, waittime):
    self.control_event.wait(waittime)
    if self.control_event.isSet():
      self.control_event.clear()
      if self.control_value == 0: self.kill()
      else: return self.control_value
    else:
      return False


class Animation(BlinkerThread):
  def run(self):
    ANIMTIME = 30   # seconds per animation
    while True:
      if len(self.playlist)>0:
        for anim in self.playlist:
          #TODO: check playlist after every single animation
          #TODO: get ANIMTIME (playing duration) or number of iterations from playlist
          f = xml.dom.minidom.parse(anim)
          awidth = int(f.getElementsByTagName("blm")[0].getAttribute("width"))
          aheight = int(f.getElementsByTagName("blm")[0].getAttribute("height"))
          chars = ((int(f.getElementsByTagName("blm")[0].getAttribute("bits"))+3)//4)*int(f.getElementsByTagName("blm")[0].getAttribute("channels"))
          starttime = time.time()
          while time.time() < starttime + ANIMTIME:
            for frame in f.getElementsByTagName("frame"):
              duration = int(frame.getAttribute("duration"))
              lightdata = []
              for row in frame.getElementsByTagName("row"): 
                rowdata = row.firstChild.nodeValue
                for i in range(awidth):
                  lightdata.append(chr(int(rowdata[i*chars:(i+1)*chars], 16)))
              self.send(lightdata)
              self.wait(duration / 1000.0)
      else:
        self.wait(1)

class Lauftext(BlinkerThread):
  def __init__(self, *args, **kwargs):
    BlinkerThread.__init__(self, *args)
    self.text = kwargs["text"]
  def run(self):
    DELAY = 0.14
    import text
    textwidth = text.getWidth(self.text)
    for offset in range(self.width, -textwidth-1, -1):
      text.showtext(self, self.text, offset)
      self.wait(DELAY)

class Lukas(BlinkerThread):
  def run(self):
    lukasmeter = 0
    self.display(0)
    while True:
      self.control_event.wait()
      self.control_event.clear()
      if self.control_value == 0:
        self.kill()
      elif self.control_value == 100:
        while lukasmeter > 0:
          lukasmeter -= 1
          self.display(lukasmeter)
          self.wait(0.2)
      else:
        lukasmeter = 0
        while lukasmeter < self.control_value * self.height and lukasmeter < self.height:
          lukasmeter += 1
          self.display(lukasmeter)
          self.wait(0.1)

  def display(self, pixels):
    self.send((self.height-pixels)*"\x00\x00" + pixels*"\x00\x01")
        
  def hau(self, value):
    self.control_value = value
    self.control_event.set()

  def reset(self):
    self.control_value = 100
    self.control_event.set()

