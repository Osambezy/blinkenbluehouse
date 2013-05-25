import threading
import sys
import time
import socket

import mcuf
import blthreads.text as text

class BlinkerThread(threading.Thread):

    def __init__(self, width, height, mcu_socket):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.control_event = threading.Event()
        self.control_value = 0
        self.mcu_socket = mcu_socket
        self.width = width
        self.height = height

    def run(self):
        """Do the main action of the thread.

        Must be overridden in subclasses.
        """
        raise NotImplementedError

    def send(self, light_data):
        """Send light data to the MCU.

        Arguments:
        light_data -- A byte string containing boolean light data, one byte
                      per lamp
        """
        data = mcuf.packet_bool(light_data, self.width, self.height)
        try:
            self.mcu_socket.send(data)
        except socket.error:
            pass

    def clear(self):
        """Send an all-off packet to the MCU."""
        data = mcuf.packet_alloff(self.width, self.height)
        try:
            self.mcu_socket.send(data)
        except socket.error:
            pass

    def wait(self, wait_time):
        """Wait for specified time.

        Always use this method instead of time.sleep() so that the thread can
        be stopped via a control_event while it is waiting.

        Arguments:
        wait_time -- time to wait in seconds
        """
        while True:
            waitstart = time.time()
            self.control_event.wait(wait_time)
            if not self.control_event.isSet():
                return
            self.control_event.clear()
            if self.control_value == 0:
                self._kill()
            else:
                wait_time -= time.time() - waitstart
                if wait_time <= 0:
                    return

    def stop(self):
        """Stop the thread.

        The thread's control event is set to notify waiting loops.  Then join()
        is called to block until the the thread has really finished.
        It is safe to call multiple times.
        """
        self.control_value = 0
        self.control_event.set()
        self.join()

    def _kill(self):
        """Clear the output and exit() the current thread.

        Should only be called internally from waiting functions after the
        control event indicates to stop the thread.
        """
        self.clear()
        sys.exit()


class EmptyThread(BlinkerThread):

    def run(self):
        pass


class Game(BlinkerThread):

    def __init__(self, width, height, mcu_socket, game_column=0):
        BlinkerThread.__init__(self, width, height, mcu_socket)
        self.col = game_column
        self.controls = []

    def keypress(self, keysym):
        if keysym in self.controls:
            self.control_value = self.controls.index(keysym) + 1
            self.control_event.set()

    def waitforkey(self, waittime, key):
        while True:
            waitstart = time.time()
            self.control_event.wait(waittime)
            if not self.control_event.isSet():
                return False
            self.control_event.clear()
            if self.control_value == 0:
                self._kill()
            elif self.control_value == key:
                return True
            else:
                waittime -= time.time() - waitstart
                if waittime <= 0:
                    return False

    def waitforanykey(self, waittime):
        self.control_event.wait(waittime)
        if not self.control_event.isSet():
            return False
        self.control_event.clear()
        if self.control_value == 0:
            self._kill()
        else:
            return self.control_value


class Animation(BlinkerThread):

    def __init__(self, *args, **kwargs):
        BlinkerThread.__init__(self, *args)
        self.playlist = kwargs['pl']
        self.playlist.animStart()

    def run(self):
        while True:
            (lightdata, duration) = self.playlist.getNextFrame()
            self.send(lightdata)
            self.wait(duration / 1000.0)


class ScrollingText(BlinkerThread):

    def __init__(self, *args, **kwargs):
        BlinkerThread.__init__(self, *args)
        self.text = kwargs['text']

    def run(self):
        DELAY = 0.14
        textwidth = text.getWidth(self.text)
        for offset in range(self.width, -textwidth - 1, -1):
            text.showtext(self, self.text, offset)
            self.wait(DELAY)


class Lukas(BlinkerThread):

    def __init__(self, *args, **kwargs):
        BlinkerThread.__init__(self, *args)
        self.col = kwargs['lukas_column']

    def run(self):
        lukasmeter = 0
        self.display(0)
        while True:
            self.control_event.wait()
            self.control_event.clear()
            if self.control_value == 0:
                self._kill()
            elif self.control_value == 100:
                while lukasmeter > 0:
                    lukasmeter -= 1
                    self.display(lukasmeter)
                    self.wait(0.2)
            else:
                lukasmeter = 0
                while lukasmeter < self.control_value * self.height and \
                        lukasmeter < self.height:
                    lukasmeter += 1
                    self.display(lukasmeter)
                    self.wait(0.1)

    def display(self, pixels):
        self.send((self.height - pixels) * self.width * '\x00' +
                  pixels * (self.col * '\x00' + '\x01' +
                  (self.width - self.col - 1) * '\x00'))

    def hau(self, value):
        self.control_value = value
        self.control_event.set()

    def reset(self):
        self.control_value = 100
        self.control_event.set()
