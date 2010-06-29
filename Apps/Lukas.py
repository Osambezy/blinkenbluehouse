import socket, time, threading, serial

CCC_HOST = '10.150.89.11'
#CCC_HOST = '10.150.86.39'
#CCC_HOST = '192.168.42.1'
#CCC_HOST = "localhost"
CCC_PORT = 5000

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

myport = serial.Serial("/dev/ttyUSB0")

myport.setRTS(0)
myport.setDTR(1)

class Heartbeat(threading.Thread):
  def __init__(self, ccc_socket):
    threading.Thread.__init__(self)
    self.setDaemon(True)
    self.ccc_socket = ccc_socket
  def run(self):
    while True:
      try: self.ccc_socket.send("HB")
      except socket.error: pass
      time.sleep(1)

def send(what):
  try:
    net.send(what)
  except socket.error:
    pass

#hb = Heartbeat(net)
#hb.start()

lukas_time = 1.0

while True:
  send("LU0")
  print "reset"
  while myport.getDSR(): pass
  starttime = time.time()
  while not myport.getCTS(): 
    lukas_time = time.time() - starttime
    if lukas_time > 0.5: break
  if lukas_time < 0.5:
    lukas = 0.005 / lukas_time
    send("LU" + str(lukas))
    print str(int(lukas*100)) + "%"
  while not myport.getDSR(): pass


