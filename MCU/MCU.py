import math
import socket
import time
import struct
import sys
import threading
import xml.dom.minidom
from itertools import product

from bus import RS485, UDP2RS485

HOST = 'localhost'
PORT = 2323
FORMAT = 'mcuf'  # supported: 'blp', 'mcuf'


class MatrixSetup:

    def __init__(self, filename=None):
        self.bus_controls = dict()
        self.bus_mappings = []
        (buses, mapping, self.width, self.height) = \
                self.read_from_file(filename)
        if len(mapping) != self.width * self.height:
            raise Exception('Error in mapping table')
        for mybus in buses.items():
            if mybus[1][0] == 'serial':
                self.bus_controls[mybus[0]] = RS485(mybus[1][1],
                                                    int(mybus[1][2]))
            elif mybus[1][0] == 'udp2serial':
                self.bus_controls[mybus[0]] = UDP2RS485(mybus[1][1],
                                                        int(mybus[1][2]))
            elif mybus[1][0] == 'dummy':
                self.bus_controls[mybus[0]] = None
            else:
                raise Exception('Unknown bus type')
        self.bus_mappings = [dict() for i in range(len(buses))]
        for i in range(len(mapping)):
            bus, box = mapping[i][0], mapping[i][1]
            if not buses[bus][0] == 'dummy':
                if not box in self.bus_mappings[bus].keys():
                    self.bus_mappings[bus][box] = []
                self.bus_mappings[bus][box] += [(i, mapping[i][2],
                                                 mapping[i][3], mapping[i][4])]

    def read_from_file(self, filename):
        dummy = ({0: ('dummy',)},
                 15 * 15 * ((0, 0, 0, 1, 1),),
                 15,
                 15)
        if filename is None:
            print 'No mapping file specified, using dummy output.'
            return dummy
        else:
            try:
                mapfile = xml.dom.minidom.parse(filename)
            except IOError:
                print 'Mapping file not found, using dummy output.'
                return dummy
        buslist = dict()
        for bus in mapfile.getElementsByTagName('bus'):
            buslist[int(bus.getAttribute('id'))] = (bus.getAttribute('type'),
                                                    bus.getAttribute('param1'),
                                                    bus.getAttribute('param2'))
        mapping = []
        for p in mapfile.getElementsByTagName('pixel'):
            if p.hasAttribute('format'):
                format = p.getAttribute('format')
            else:
                format = 'bw'
            if format == 'bw':
                channels, maxval = 1, 1
            elif format == 'grey':
                channels, maxval = 1, 255
            elif format == 'rgb':
                channels, maxval = 3, 255
            mapping.append((int(p.getAttribute('bus')),
                            int(p.getAttribute('box')),
                            int(p.getAttribute('port')), channels, maxval))
        root_elem = mapfile.getElementsByTagName('mapping')[0]
        w = int(root_elem.getAttribute('width'))
        h = int(root_elem.getAttribute('height'))
        return (buslist, mapping, w, h)


class Sender(threading.Thread):

    """The Sender() thread handles output to the buses.  The minimum output
    rate can be set via the interval argument.  The output rate can of course
    be higher as more data arrives.
    """

    def __init__(self, setup, interval=0.2):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.lock = threading.Lock()
        self.setup = setup
        self.interval = interval
        self.updated = False
        self.data = self.setup.width * self.setup.height * '\x00'
        self.channels = 1
        self.maxval = 1

    def run(self):
        while True:
            time.sleep(self.interval)
            self.lock.acquire()
            if self.updated:
                self.updated = False
            else:
                self.output_bus()
            self.lock.release()

    def resize_frame(self, data, width, height, channels, maxval):
        if len(data) != width * height * channels:
            raise ValueError('wrong dimensions')
        width = float(width)
        height = float(height)
        maxval = float(maxval)
        new_data = ''
        y_ratio = height / self.setup.height
        x_ratio = width / self.setup.width
        for (new_y, new_x) in product(range(0, self.setup.height),
                                      range(0, self.setup.width)):
            value = 0.0
            for (y, x) in product(range(int(math.floor(y_ratio * new_y)),
                                        int(math.ceil(y_ratio * (new_y + 1)))),
                                  range(int(math.floor(x_ratio * new_x)),
                                       int(math.ceil(x_ratio * (new_x + 1))))):
                weight = 1.0
                if y < y_ratio * new_y:
                    weight *= y + 1 - (y_ratio * new_y)
                elif y > y_ratio * (new_y + 1) - 1:
                    weight *= y_ratio * (new_y + 1) - y
                if x < x_ratio * new_x:
                    weight *= x + 1 - (x_ratio * new_x)
                elif x > x_ratio * (new_x + 1) - 1:
                    weight *= x_ratio * (new_x + 1) - x
                value += ord(data[y * int(width) + x]) / maxval / \
                    y_ratio / x_ratio * weight
            new_data += chr(int(math.floor(value * maxval + 0.5)))
        return new_data

    def output(self, data, width, height, channels, maxval):
        self.lock.acquire()
        self.updated = True
        if len(data) != width * height * channels:
            raise ValueError('wrong dimensions')
        if width != self.setup.width or height != self.setup.height:
            print 'Resizing %dx%d to %dx%d' % \
                (width, height, self.setup.width, self.setup.height)
            data = self.resize_frame(data, width, height, channels, maxval)
        self.data, self.channels, self.maxval = data, channels, maxval
        self.output_bus()
        self.lock.release()

    def output_bus(self):
        for b in range(len(self.setup.bus_controls)):
            box_data_list = []
            for box in self.setup.bus_mappings[b].keys():
                lamps = []
                for lamp in self.setup.bus_mappings[b][box]:
                    lampdata = self.data[lamp[0] * self.channels:
                                         (lamp[0] + 1) * self.channels]
                    if self.channels == 1 and lamp[2] == 3:
                        lampdata = 3 * lampdata
                    elif self.channels == 3 and lamp[2] == 1:
                        lampdata = chr((ord(lampdata[0]) + ord(lampdata[1]) +
                                        ord(lampdata[2])) / 3)
                    if self.maxval != lamp[3]:
                        for c in range(len(lampdata)):
                            lampdata = lampdata[:c] + \
                                chr(int(float(ord(lampdata[c])) /
                                        self.maxval * lamp[3])) + \
                                lampdata[c + 1:]
                    lamps += [(lamp[1], lamp[2], lamp[3], lampdata)]
                box_data_list += [(box, lamps)]
            if len(box_data_list) > 0:
                self.setup.bus_controls[b].output(box_data_list)


class MCU:

    def __init__(self):
        if len(sys.argv) > 1:
            setup = MatrixSetup(sys.argv[1])
        else:
            setup = MatrixSetup()
        self.sender = Sender(setup)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if HOST == 'localhost':
            self.socket_mode = 'server'
            self.socket.bind(('', PORT))
            print 'Waiting for data'
        else:
            self.socket_mode = 'client'
            self.socket.connect((HOST, PORT))
            print 'Requesting %s stream from %s:%d' % \
                (FORMAT.upper(), HOST, PORT)
        self.socket.settimeout(1)

    def handle_packet(self, data):
        # Clear console.
        print '\x1b\x5b\x48\x1b\x5b\x32\x4a'
        if len(data) >= 12 and data.startswith('\xDE\xAD\xBE\xEF'):
            frame_num, width, height = struct.unpack('>LHH', data[4:12])
            channels, maxval = 1, 1
            pixel_data = data[12:]
            print 'BLP frame received, frame #%d, width: %d, height: %d' %\
                (frame_num, width, height)
            FORMAT = 'blp'
        if len(data) >= 12 and data.startswith('\x23\x54\x26\x66'):
            height, width, channels, maxval = struct.unpack('>HHHH',
                                                            data[4:12])
            pixel_data = data[12:]
            print 'MCUF frame received, width: %d, height: %d' % \
                (width, height)
            FORMAT = 'mcuf'
        else:
            print 'invalid data received'
            return
        # Do some sanity checks on received frame.
        if len(pixel_data) != width * height * channels:
            print 'Warning: wrong length of pixel data! ' \
                  'Frame filled/cropped.'
            pixel_data += width * height * channels * '\x00'
            pixel_data = pixel_data[:width * height * channels]
        for p in range(len(pixel_data)):
            if ord(pixel_data[p]) > maxval:
                print 'Warning: brightness of pixel #%d is ' \
                      'greater than specified maximum value' % (p,)
                pixel_data = pixel_data[:p] + chr(maxval) + \
                    pixel_data[p + 1:]
        if channels != 1 and channels != 3:
            print 'Warning: unsupported number of channels: %d, ' \
                  'using only first channel' % (channels,)
            new_pixel_data = ''
            for p in range(width * height):
                new_pixel_data += pixel_data[p * channels]
            pixel_data = new_pixel_data
            channels = 1
        # Display received frame on console.
        display_frame = ''
        for i in range(height):  # TODO: mix down rgb
            display_frame += '  '
            for j in range(width):
                if ord(pixel_data[(i * width + j) * channels]) < \
                        maxval / 2.0:
                    display_frame += '.. '
                else:
                    display_frame += '## '
            display_frame += '\x0A'
        print display_frame
        last_received = time.time()
        # Hand the frame data over to the sender thread.
        self.sender.output(pixel_data, width, height, channels, maxval)

    def mainloop(self):
        last_refresh = 0
        last_received = 0
        self.sender.start()
        while True:
            if (last_refresh <= time.time() - 10 or \
                    (last_received <= time.time() - 20 and \
                     last_refresh <= time.time() - 1)) and \
                    self.socket_mode == 'client':
                if FORMAT == 'mcuf':
                    self.socket.send(
                        '\x42\x42\x42\x42\x00\x00\x00\x00\x00\x00\x00\x00')
                else:
                    self.socket.send('\xDE\xAD\xBE\xCDREFRESH')
                last_refresh = time.time()
            try:
                data = self.socket.recv(1024)
            except (socket.error, socket.timeout):
                pass
            except KeyboardInterrupt:
                break
            else:
                self.handle_packet(data)
        print 'Shutting down'
        self.socket.settimeout(5)
        if self.socket_mode == 'client':
            if FORMAT == 'mcuf':
                self.socket.send(
                    '\x42\x42\x42\x43\x00\x00\x00\x00\x00\x00\x00\x00')
            else:
                self.socket.send('\xDE\xAD\xBE\xCDCLOSE')
        self.socket.close()


if __name__ == '__main__':
    mcu = MCU()
    mcu.mainloop()
