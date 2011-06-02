import socket, time, serial, random, os, sys
from wave import open as waveOpen
from ossaudiodev import open as ossOpen
try:
  from ossaudiodev import AFMT_S16_NE
except ImportError:
  if byteorder == "little":
    AFMT_S16_NE = ossaudiodev.AFMT_S16_LE
  else:
    AFMT_S16_NE = ossaudiodev.AFMT_S16_BE

CCC_HOST = "localhost"
CCC_PORT = 5000
SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUD = 9600

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

myport = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD)

dsp = ossOpen('/dev/dsp','w')
low = ['low1.wav', 'low2.wav', 'low3.wav', 'low4.wav']
med = ['med1.wav', 'med2.wav', 'med3.wav', 'med4.wav']
high = ['high1.wav', 'high2.wav', 'high3.wav', 'high4.wav']
top = ['top1.wav', 'top2.wav']
intro = ['intro1.wav', 'intro2.wav']

def send(what):
  try:
    net.send(what)
  except socket.error:
    pass

def play_sound(filename):
  try: s = waveOpen(os.path.abspath(os.path.dirname(sys.argv[0]))+'/lukas-sounds/'+filename,'rb')
  except: print "Sound file not found"
  else:
    (nc,sw,fr,nf,comptype, compname) = s.getparams( )
    dsp.setparameters(AFMT_S16_NE, nc, fr)
    dsp.write(s.readframes(nf))
    s.close()

min_lukas = 0.01
min_t = 50.0

A = (1.0-min_lukas) / ((1.0/min_t) - (1.0/255.0))
B = (1.0-min_lukas) / (1.0 - (min_t/255.0)) - 1.0

send("LU0")

try:
  while True:
    #play_sound(random.choice(intro))
    lukas_time = ord(myport.read())
    if lukas_time > 0:
      print "Zeit: %d" % (lukas_time)
      lukas =  A / lukas_time - B
      send("LU" + str(lukas))
      print str(int(lukas*100)) + "%"
      if lukas>=6.0/7: play_sound(random.choice(top))
      elif lukas>=4.0/7: play_sound(random.choice(high))
      elif lukas>=2.0/7: play_sound(random.choice(med))
      else: play_sound(random.choice(low))
      time.sleep(2)
      send("LU0")
      print "reset"
except KeyboardInterrupt:
  dsp.close()

