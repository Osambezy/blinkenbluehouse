import bus

import serial
import time

class RS485(bus.Bus):
  def __init__(self, port, baudrate):
    self.port = port
    self.baudrate = baudrate
    self.myport = None

    self.open_port(retry=False)

  def open_port(self, retry):
    while True:
      print "Opening serial port " + self.port + " ...  ",
      try:
        self.myport = serial.Serial(self.port, self.baudrate)
        print "ok"
        break
      except serial.SerialException:
        print "failed"
        if retry:
          try: time.sleep(2)
          except KeyboardInterrupt: exit()
        else:
          break

  def __del__(self):
    try: self.myport.close()
    except AttributeError: pass

  def send(self, data):
    try:
      #self.myport.flushOutput()
      self.myport.write(data)
    except (serial.SerialException, AttributeError):
      print "Error: serial port not available, trying to reopen...  ",
      try: self.myport.close()
      except: pass
      self.open_port(False)

