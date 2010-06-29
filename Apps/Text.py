import socket, time, threading
from Tkinter import *

#CCC_HOST = '10.150.89.11'
#CCC_HOST = '192.168.42.1'
CCC_HOST = "localhost"
CCC_PORT = 5000

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

root = Tk()
root.title("BlinkenBlueHouse-Text-Box")
textfeld = Entry(root,width=40)
def sendtext():
  global textfeld
  net.send("TX" + textfeld.get())
button = Button(root,text="anzeigen",command=sendtext)
textfeld.pack()
button.pack()
root.mainloop()
