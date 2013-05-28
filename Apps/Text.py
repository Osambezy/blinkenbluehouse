import socket
import time
import threading
from Tkinter import *

CCC_HOST = 'localhost'
CCC_PORT = 5000

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

root = Tk()
root.title('BlinkenBlueHouse-Text-Box')
textbox = Entry(root, width=40)


def sendtext():
    global textbox
    net.send('TX' + textbox.get())
button = Button(root, text='Send text', command=sendtext)
textfeld.pack()
button.pack()
root.mainloop()
