import os
import xml.dom.minidom
from threading import Lock

class Playlist():

  def __init__(self, basepath, WIDTH, HEIGHT):
    self.basepath, self.WIDTH, self.HEIGHT = basepath, WIDTH, HEIGHT
    self.request_id = 0
    self.pos_id = 0
    self.pos_repeat = 0
    self.pos_frame = -1
    self.lock = Lock()
    self.updateAvailable()
    self.list = []
    for i in range(len(self.available)):
      self.add(i)

  def updateAvailable(self):
    self.available = []
    path = self.basepath + "/animations/" + str(self.WIDTH) + "x" + str(self.HEIGHT) + "/"
    try:
      anims = os.listdir(path)
    except OSError:
      print "No animations available for " + str(self.WIDTH) + "x" + str(self.HEIGHT)
    else:
      for anim in anims:
        f = xml.dom.minidom.parse(path+"/"+anim)
        try: title = f.getElementsByTagName("header")[0].getElementsByTagName("title")[0].firstChild.data
        except (IndexError, AttributeError): title = anim[:-4]
        try: desc = f.getElementsByTagName("header")[0].getElementsByTagName("description")[0].firstChild.data
        except (IndexError, AttributeError): desc = ""
        if self.WIDTH != int(f.getElementsByTagName("blm")[0].getAttribute("width")) or self.HEIGHT != int(f.getElementsByTagName("blm")[0].getAttribute("height")):
          print "Warning: Animation dimensions don't match matrix size! Using anyway..."
        self.available.append((title, desc, f))
    self.available.sort()
    self.request_id += 1

  def animStart(self):
    # nach Geschmack: Playlist von vorn beginnen etc.
    pass

  def next_id(self):
    self.pos_id = self.pos_id + 1
    if self.pos_id >= len(self.list): self.pos_id = 0

  def next_repeat(self):
    self.pos_repeat = self.pos_repeat + 1
    try: repeats = self.list[self.pos_id][1]
    except IndexError: repeats = 0
    if self.pos_repeat >= repeats:
      self.pos_repeat = 0
      self.next_id()

  def next_frame(self):
    self.pos_frame = self.pos_frame + 1
    try: frames = len(self.list[self.pos_id][0][2].getElementsByTagName("frame"))
    except (AttributeError, IndexError): frames = 0
    if self.pos_frame >= frames:
      self.pos_frame = 0
      self.next_repeat()

  def getNextFrame(self):
    if len(self.list)==0: return (self.WIDTH*self.HEIGHT*'\x00', 1000)
    self.next_frame()
    anim = self.list[self.pos_id][0][2]
    chars = ((int(anim.getElementsByTagName("blm")[0].getAttribute("bits"))+3)//4)*int(anim.getElementsByTagName("blm")[0].getAttribute("channels"))
    frame = anim.getElementsByTagName("frame")[self.pos_frame]
    duration = int(frame.getAttribute("duration"))
    lightdata = []
    for row in frame.getElementsByTagName("row"): 
      rowdata = row.firstChild.data
      for i in range(len(rowdata)//chars):
        lightdata.append(chr(int(rowdata[i*chars:(i+1)*chars], 16)))
    return (lightdata, duration)

  def move_down(self, n):
    if n>=0 and n<len(self.list)-1:
      self.list[n], self.list[n+1] = self.list[n+1], self.list[n]
      self.request_id += 1
  def inc_repeats(self, n):
    if n>=0 and n<len(self.list):
      self.list[n][1] += 1
      self.request_id += 1
  def dec_repeats(self, n):
    if n>=0 and n<len(self.list):
      if self.list[n][1] > 1:
        self.list[n][1] -= 1
        self.request_id += 1
  def remove(self, n):
    if n>=0 and n<len(self.list):
      del self.list[n]
      self.request_id += 1
  def add(self, avail_n):
    if avail_n>=0 and avail_n<len(self.available):
      self.list.append([self.available[avail_n], 10])
      self.request_id += 1
