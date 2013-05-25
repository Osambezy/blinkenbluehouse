import serial
import time

import bus


class RS485(bus.Bus):

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.myport = None
        self.open_port(retry=False)

    def open_port(self, retry):
        while True:
            print "Opening serial port %s ...  " % (self.port,),
            try:
                self.myport = serial.Serial(self.port, self.baudrate)
            except serial.SerialException:
                print "failed"
                if retry:
                    try:
                        time.sleep(2)
                    except KeyboardInterrupt:
                        exit()
                else:
                    break
            else:
                print "ok"
                break

    def __del__(self):
        try:
            self.myport.close()
        except AttributeError:
            pass

    def send(self, data):
        try:
            self.myport.write(data)
        except Exception:  # no exception name given, serial port errors come in many different unexpected flavors!
            print "Error: serial port not available, trying to reopen...  ",
            try:
                self.myport.close()
            except Exception:
                pass
            self.open_port(retry=False)
