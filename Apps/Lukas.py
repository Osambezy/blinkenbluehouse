import socket, time, serial

CCC_HOST = "localhost"
#CCC_HOST = '10.150.89.40'
#CCC_HOST = '10.150.86.39'
CCC_PORT = 5000

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

myport = serial.Serial("/dev/ttyACM0")
#myport = serial.Serial("/dev/ttyUSB0")
myport.baudrate = 9600

def send(what):
  try:
    net.send(what)
  except socket.error:
    pass

lukas_time = 1.0

while True:
  send("LU0")
  print "reset"
  lukas_time = float(ord(myport.read()))
  print "Zeit: %d" % (lukas_time)
  lukas =  50 / lukas_time
  send("LU" + str(lukas))
  print str(lukas) + "%"
  time.sleep(2)


# old method (polling serial control lines):

#myport.setRTS(0)
#myport.setDTR(1)

#  while myport.getDSR(): pass
#  starttime = time.time()
#  while not myport.getCTS(): 
#    lukas_time = time.time() - starttime
#    if lukas_time > 0.5: break
#  if lukas_time < 0.5:
#    lukas = 0.005 / lukas_time
#    send("LU" + str(lukas))
#    print str(int(lukas*100)) + "%"
#  while not myport.getDSR(): pass

