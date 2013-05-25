import socket
import time
import threading
from Tkinter import *

CCC_HOST = 'localhost'
CCC_PORT = 5000

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))


def send(what):
    try:
        net.send(what)
    except socket.error:
        print 'Socket error'


def sendkey(event):
    if event.keysym == 'F1':
        send('OF')
    elif event.keysym == 'F2':
        send('ON')
    elif event.keysym == 'F3':
        send('AN')
    elif event.keysym == 'F4':
        send('VU')
    elif event.keysym == 'F5':
        send('INsnake')
    elif event.keysym == 'F6':
        send('INtetris')
    elif event.keysym == 'F7':
        send('INmaze')
    elif event.keysym == 'F8':
        send('INpong')
    elif event.keysym == '1':
        send('TG00')
    elif event.keysym == '2':
        send('TG01')
    elif event.keysym == '3':
        send('TG02')
    else:
        send('ID' + event.keysym)
    print 'Sent "%s"' % (event.keysym, )


class Heartbeat(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            send('HB')
            time.sleep(1)


root = Tk()
root.title('BlinkenBlueHouse-Interactive-Box')
dingsbums = Label(root, text='whiaschaotsaus?', width=40, height=10)
dingsbums.pack()
root.bind('<Key>', sendkey)
hb = Heartbeat()
hb.start()
root.mainloop()
