import socket, time, threading
from Tkinter import *

#CCC_HOST = '10.150.89.11'
#CCC_HOST = '10.150.86.37'
#CCC_HOST = '192.168.42.1'
CCC_HOST = "localhost"
CCC_PORT = 5000

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

def sendkey(event):
  try:
    if event.keysym == "F1": net.send("OF")
    elif event.keysym == "F2": net.send("ON")
    elif event.keysym == "F3": net.send("AN")
    elif event.keysym == "F4": net.send("VU")
    elif event.keysym == "F5": net.send("INsnake")
    elif event.keysym == "F6": net.send("INtetris")
    elif event.keysym == "F7": net.send("INmaze")
    elif event.keysym == "F8": net.send("INpong")
    elif event.keysym == "F10": net.send("V+")
    else:
      net.send("ID" + event.keysym)
    print 'Sent "'+event.keysym+'"'
  except socket.error: print "Socket error"

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

root = Tk()
root.title("BlinkenBlueHouse-Interactive-Box")
dingsbums = Label(root,text="whiaschaotsaus?",width=40,height = 10)
dingsbums.pack()
root.bind('<Key>',sendkey)
hb = Heartbeat(net)
hb.start()
root.mainloop()
