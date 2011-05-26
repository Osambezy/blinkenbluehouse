import socket, time, serial

CCC_HOST = "localhost"
CCC_PORT = 5000
SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUD = 9600

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

myport = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD)

def send(what):
  try:
    net.send(what)
  except socket.error:
    pass

min_lukas = 0.01
min_t = 50.0

A = (1.0-min_lukas) / ((1.0/min_t) - (1.0/255.0))
B = (1.0-min_lukas) / (1.0 - (min_t/255.0)) - 1.0

while True:
  send("LU0")
  print "reset"
  lukas_time = ord(myport.read())
  print "Zeit: %d" % (lukas_time)
  lukas =  A / lukas_time - B
  send("LU" + str(lukas))
  print str(int(lukas*100)) + "%"
  time.sleep(2)

