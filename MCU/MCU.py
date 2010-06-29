import bus

import math
import socket
import time
import struct
import sys

#HOST = '10.150.86.34'
#PORT = 4242
HOST ='localhost'
PORT = 2323
FORMAT = "mcuf"  # supported: 'blp', 'mcuf'

def init_mapping():
  global TARGET_WIDTH, TARGET_HEIGHT, TARGET_MAXVAL, bus_controls, bus_mappings

  TARGET_WIDTH = 15
  TARGET_HEIGHT = 15
  buses = (('dummy',),)
  mapping = TARGET_WIDTH*TARGET_HEIGHT*((0,0,0),)

  TARGET_MAXVAL = 1 # TODO: lamp specific

  try:
    filename = sys.argv[1]
    (buses, mapping, TARGET_WIDTH, TARGET_HEIGHT) = read_mapping(filename)
  except IndexError:
    print "No mapping file specified, using dummy output."
  except IOError:
    print "Mapping file not found, using dummy output."

  if TARGET_WIDTH<1 or TARGET_HEIGHT<1 or TARGET_MAXVAL<1: raise Exception, "Illegal values in mapping file"
  if len(mapping) != TARGET_WIDTH*TARGET_HEIGHT: raise Exception, "Error in mapping table"
  bus_controls = []
  for mybus in buses:
    if mybus[0] == "serial":
      bus_controls += [bus.RS485(mybus[1], int(mybus[2]))]
    elif mybus[0] == "udp2serial":
      bus_controls += [bus.UDP2RS485(mybus[1], int(mybus[2]))]
    elif mybus[0] == "dummy":
      bus_controls += [None]
    else:
      raise Exception, "Unknown bus type"
  bus_mappings = len(buses) * [dict()]
  for i in range(len(mapping)):
    if not buses[mapping[i][0]][0] == "dummy":
      if not mapping[i][1] in bus_mappings[mapping[i][0]].keys():
        bus_mappings[mapping[i][0]][mapping[i][1]] = []
      bus_mappings[mapping[i][0]][mapping[i][1]] += [(mapping[i][2], i)]

def read_mapping(filename):
  import xml.dom.minidom
  mapfile = xml.dom.minidom.parse(filename)
  buslist = [(bus.getAttribute("type"), bus.getAttribute("param1"), bus.getAttribute("param2")) for bus in mapfile.getElementsByTagName("bus")]
  mapping = [(int(p.getAttribute("bus")), int(p.getAttribute("box")), int(p.getAttribute("port"))) for p in mapfile.getElementsByTagName("pixel")]
  w = int(mapfile.getElementsByTagName("mapping")[0].getAttribute("width"))
  h = int(mapfile.getElementsByTagName("mapping")[0].getAttribute("height"))
  #TARGET_MAXVAL    lamp specific!
  return (buslist, mapping, w, h)

def init_network():
  global net, MODE
  net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  if HOST=='localhost':
    MODE = "server"
    net.bind(('', PORT))
  else:
    MODE = "client"
    net.connect((HOST, PORT))

  if MODE == "client": print 'Requesting '+FORMAT.upper()+' stream from '+HOST+':'+str(PORT)
  else: print "Waiting for data"
  net.settimeout(1)

def mainloop():
  global net, MODE
  last_refresh = 0
  last_received = 0
  while True:
    if (last_refresh<=time.time()-10 or (last_received<=time.time()-20 and last_refresh<=time.time()-1)) and MODE=="client":
      if FORMAT == "mcuf": net.send('\x42\x42\x42\x42\x00\x00\x00\x00\x00\x00\x00\x00')
      else: net.send('\xDE\xAD\xBE\xCDREFRESH')
      last_refresh = time.time()
    try: data = net.recv(1024)
    except (socket.error, socket.timeout): pass
    except KeyboardInterrupt: break
    else:
      print "\x1b\x5b\x48\x1b\x5b\x32\x4a" # clear terminal
      if len(data)>=12 and data[0:4]=='\xDE\xAD\xBE\xEF':
        frame_num,width,height = struct.unpack(">LHH", data[4:12])
        channels,maxval = 1,1
        pixel_data = data [12:]
        print "BLP frame received, frame #"+str(frame_num)+", width: "+str(width)+", height: "+str(height)
        FORMAT = 'blp'
      if len(data)>=12 and data[0:4]=='\x23\x54\x26\x66':
        height,width,channels,maxval = struct.unpack(">HHHH", data[4:12])
        pixel_data = data [12:]
        print "MCUF frame received, width: "+str(width)+", height: "+str(height)
        FORMAT = 'mcuf'
      else:
        print "invalid data received"
        continue
      if len(pixel_data) != width*height*channels:
        print "Warning: wrong length of pixel data! Frame filled/cropped."
        pixel_data = (pixel_data + width*height*channels*"\x00")[0:width*height*channels]
      display_frame = ""
      for i in range(0,height):
        display_frame += "  "
        for j in range(0,width): display_frame += pixel_data[i*width+j].replace("\x00",".. ").replace("\x01","## ")
        display_frame += "\x0A"
      print display_frame
      last_received = time.time()
      if channels != 1:
        print "Error: got "+str(channels)+" channels, but only 1 supported"
      else:
        output(pixel_data, width, height, maxval)

def quit():
  print "Shutting down"
  net.settimeout(5)
  if MODE == "client":
    if FORMAT == "mcuf": net.send('\x42\x42\x42\x43\x00\x00\x00\x00\x00\x00\x00\x00')
    else: net.send('\xDE\xAD\xBE\xCDCLOSE')
  net.close()

def output(data, width=0, height=0, maxval=0):
  global TARGET_WIDTH, TARGET_HEIGHT, TARGET_MAXVAL
  if width==0: width= TARGET_WIDTH
  if height==0: width= TARGET_HEIGHT
  if maxval==0: width= TARGET_MAXVAL
  if len(data) != width * height: raise ValueError, "wrong dimensions"
  if width != TARGET_WIDTH or height != TARGET_HEIGHT or maxval != TARGET_MAXVAL:
    print "Resizing "+str(width)+"x"+str(height)+" to "+str(TARGET_WIDTH)+"x"+str(TARGET_HEIGHT)
    data = resize_frame(data, width, height, maxval)

  for b in range(len(bus_controls)):
    box_data_list = []
    for box in bus_mappings[b].keys():
      lamps = []
      for lamp in bus_mappings[b][box]:
        lamps += [(lamp[0], TARGET_MAXVAL, ord(data[lamp[1]]))]
      box_data_list += [(box, lamps)]
    if len(box_data_list) > 0:
      bus_controls[b].output(box_data_list)

def resize_frame(data, width, height, maxval=255):
  global TARGET_WIDTH, TARGET_HEIGHT, TARGET_MAXVAL
  if len(data) != width * height: raise ValueError, "wrong dimensions"
  width = float(width)
  height = float(height)
  maxval = float(maxval)
  new_data = ''
  y_ratio = height/TARGET_HEIGHT
  x_ratio = width/TARGET_WIDTH
  for new_y in range(0,TARGET_HEIGHT):
    for new_x in range(0,TARGET_WIDTH):
      value = 0.0
      for y in range(int(math.floor(y_ratio*new_y)), int(math.ceil(y_ratio*(new_y+1)))):
        for x in range(int(math.floor(x_ratio*new_x)), int(math.ceil(x_ratio*(new_x+1)))):
          weight = 1.0
          if y<y_ratio*new_y: weight *= y+1-(y_ratio*new_y)
          elif y>y_ratio*(new_y+1)-1: weight *= y_ratio*(new_y+1)-y
          if x<x_ratio*new_x: weight *= x+1-(x_ratio*new_x)
          elif x>x_ratio*(new_x+1)-1: weight *= x_ratio*(new_x+1)-x
          value += ord(data[y*int(width)+x]) / maxval / y_ratio / x_ratio * weight
      new_data += chr(int(math.floor(value*TARGET_MAXVAL+0.5)))
  return new_data


init_mapping()
init_network()
mainloop()
quit()

