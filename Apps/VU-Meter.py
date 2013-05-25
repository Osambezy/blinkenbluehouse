import socket
import time
import math
import random
try:
    import jack
except ImportError:
    print 'PyJack is not installed. ' \
        'Go to http://sourceforge.net/projects/py-jack/\n' \
        '(needs libjack-dev and python-dev to compile)\n' \
        'using ALSA instead...'
    AUDIO_MODE = 'alsa'
    import os
    import struct
else:
    AUDIO_MODE = 'jack'
    import numpy

CCC_HOST = 'localhost'
CCC_PORT = 5000

TARGET_HEIGHT = 7
TARGET_CHANNELS = 2

UPDATE_INTERVAL = 0.1
RANDOMIZER_INTERVAL = 1.0
DECAY = 10     # decay in pixels/sec
PULLUP = 0.7   # 0 - 1
MAX_RANDOM_GAIN = 1.2
SILENCE = -70.0    # "minus infinity"
maxvolume = SILENCE
count = 0
scale_min = -20
scale_max = -0
scale_window = [0]
scale_windowsize = int(300 / UPDATE_INTERVAL)
vu_value = TARGET_CHANNELS * [0]
random_gain = TARGET_CHANNELS * [1.0]

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))
net.send('VU')
time_update = time.time()
time_random = time_update

if AUDIO_MODE == 'alsa':
    framesize = 1024
    rate = 22050
    pipe = os.popen('arecord -N -c 1 -r %d -f S16_LE' % (rate,), 'r', 0)
elif AUDIO_MODE == 'jack':
    jack.attach('VU-Meter')
    jack.register_port('in_1', jack.IsInput)
    jack.register_port('out_1', jack.IsOutput)
    jack.activate()
    # jack.connect('alsa_pcm:capture_1', 'VU-Meter:in_1')
    jack.connect('system:capture_1', 'VU-Meter:in_1')
    framesize = jack.get_buffer_size()
    rate = jack.get_sample_rate()
    input_array = numpy.zeros((1, framesize), 'f')
    output_array = numpy.zeros((1, framesize), 'f')

try:
    while True:
        if AUDIO_MODE == 'alsa':
            rms = 0.0
            frame = pipe.read(framesize * 2)  # 2 bytes per sample (16-bit)
            if len(frame) == framesize * 2:
                for sample in struct.unpack('<' + framesize * 'h', frame):
                    rms += (sample / 32768.0) ** 2
                rms = math.sqrt(rms / framesize)
            else:
                print 'Error in audio subprocess, restarting...'
                pipe.close()
                pipe = os.popen(command, 'r', 0)
        elif AUDIO_MODE == 'jack':
            try:
                jack.process(output_array, input_array)
            except (jack.InputSyncError, jack.OutputSyncError):
                print 'Jack out of sync'
            rms = math.sqrt(numpy.sum(numpy.power(input_array[0], 2)) /
                            framesize)
        if rms > 0:
            volume = math.log(rms, 1.15)
        else:
            volume = SILENCE
        if volume > maxvolume:
            maxvolume = volume
        if time.time() >= time_update:
            scaled = (maxvolume - scale_min) / (
                scale_max - scale_min) * TARGET_HEIGHT
            scaled = min(scaled, 1.3 * TARGET_HEIGHT, 254)
            if scaled < 0:
                scaled = 0
            command = 'VD'
            for ch in range(TARGET_CHANNELS):
                vu_value[ch] = vu_value[ch] - DECAY * UPDATE_INTERVAL
                if vu_value[ch] < 0:
                    vu_value[ch] = 0
                if scaled * random_gain[ch] > vu_value[ch]:
                    vu_value[ch] = (1 - PULLUP) * vu_value[
                        ch] + PULLUP * scaled * random_gain[ch]
                print int(vu_value[ch]) * 10 * ' ' + \
                    str(int(maxvolume * 10) / 10.0) + ' dB'
                command += chr(int(vu_value[ch]))
            try:
                net.send(command)
            except socket.error:
                pass
            scale_window = scale_window[-scale_windowsize:] + [maxvolume]
            mean = 0.0
            for item in scale_window:
                mean += item
            mean = mean / len(scale_window)
            stdev = 0.0
            for item in scale_window:
                stdev += (item - mean) ** 2
            stdev = math.sqrt(stdev / len(scale_window))
            scale_min, scale_max = mean - 1.5 * stdev, mean + 1.5 * stdev
            print 'Scaling: ', int(scale_min * 10) / 10.0, \
                int(scale_max * 10) / 10.0
            while time.time() >= time_update:
                time_update += UPDATE_INTERVAL
            maxvolume = SILENCE
        if time.time() >= time_random and TARGET_CHANNELS == 2:
            random_gain[0] = MAX_RANDOM_GAIN ** random.uniform(-1.0, 1.0)
            random_gain[1] = 1 / random_gain[0]
            while time.time() >= time_random:
                time_random += RANDOMIZER_INTERVAL
except KeyboardInterrupt:
    pass

if AUDIO_MODE == 'alsa':
    pipe.close()
elif AUDIO_MODE == 'jack':
    jack.deactivate()
    jack.detach()
