import socket, time, os, math, random, struct, threading, Queue
try:
  import jack
  AUDIO_MODE = "jack"
except ImportError:
  print "PyJack is not installed. Go to http://sourceforge.net/projects/py-jack/"
  print "(needs libjack-dev and python-dev to compile)"
  print "using ALSA instead..."
  AUDIO_MODE = "alsa"
else:
  import numpy

CCC_HOST = '10.150.89.194'
#CCC_HOST = "localhost"
CCC_PORT = 5000

TARGET_HEIGHT =  7
TARGET_CHANNELS = 2

net = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
net.connect((CCC_HOST, CCC_PORT))

class AudioGrabber(threading.Thread):
  def __init__(self, mode, buffersize, framesize=1024, rate=22050, format="S16_LE"):
    if format not in ["U8", "S16_LE"]:
      raise Exception, "Error: unsupported audio parameters"
    threading.Thread.__init__(self)
    self.setDaemon(True)
    self.mode = mode
    self.queue = Queue.Queue(buffersize)
    if mode=="alsa":
      self.framesize = framesize
      self.rate = rate
      self.format = format
      if self.format == "U8":
        self.fmt = (self.framesize * 1, self.framesize * "B", 128, 128)    # (number of bytes per frame, struct fmt, offset, max amplitude)
      elif self.format == "S16_LE":
        self.fmt = (self.framesize * 2, "<" + self.framesize * "h", 0, 32768)
    self.quit = False

  def run(self):
    print "Recording audio..."
    if self.mode=="alsa":
      command = "arecord -N -c 1 -r %d -f %s" % (self.rate, self.format)
      pipe = os.popen(command, "r", 0)
      while True:
        if self.quit:
          pipe.close()
          exit()
        frame = pipe.read(self.fmt[0])
        if len(frame) == self.fmt[0]:
          rms = 0.0
          for sample in struct.unpack(self.fmt[1], frame):
            rms += (float(sample - self.fmt[2]) / self.fmt[3]) ** 2
          rms = math.sqrt(rms/self.framesize)
          self.push(rms)
        else:
          print "Error in audio subprocess, restarting..."
          pipe.close()
          pipe = os.popen(command, "r", 0)

    elif self.mode=="jack": 
      jack.attach("VU-Meter")
      jack.register_port("in_1", jack.IsInput)
      jack.register_port("out_1", jack.IsOutput)
      jack.activate()
      #jack.connect("alsa_pcm:capture_1", "VU-Meter:in_1")
      jack.connect("system:capture_1", "VU-Meter:in_1")
      self.framesize = jack.get_buffer_size()
      self.rate = jack.get_sample_rate()
      input_array = numpy.zeros((1, self.framesize), 'f')
      output_array = numpy.zeros((1, self.framesize), 'f')
      time_sync = time.time()
      sync_interval = 1.0 / self.rate * self.framesize
      while True:
        time_sync += sync_interval
        try:
          time.sleep(time_sync - time.time()) # workaround because jack.process() blocks without giving control to other threads
        except IOError:
          pass
        if self.quit:
          jack.deactivate()
          jack.detach()
          exit()
        try:          
          jack.process(output_array, input_array)
        except (jack.InputSyncError, jack.OutputSyncError):
          print "Jack out of sync"
        rms = math.sqrt(numpy.sum(numpy.power(input_array[0],2))/self.framesize)
        self.push(rms)

  def push(self, value):
    try:
      self.queue.put(value, block=False)
    except Queue.Full:
      print "Buffer overflow! Reduce audio rate or increase buffer size."
      self.queue.join()
      if self.mode=="alsa": pipe.flush()

def scale_min_max(window):
  mean = 0
  for item in window: mean += item
  mean = float(mean) / len(window)
  stdev = 0
  for item in window: stdev += (item - mean)**2
  stdev = math.sqrt(float(stdev) / len(window))
  return (mean - 1.5 * stdev, mean + 1.5 * stdev)

a = AudioGrabber(mode=AUDIO_MODE, buffersize=2)
a.start()

time_update = time.time()
time_random = time_update
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
net.send("VU")

while True:
    try:
      rms = a.queue.get()
    except KeyboardInterrupt:
      a.quit = True
      a.join()
      exit()
    if rms > 0:
      volume = math.log(rms, 1.15)
    else:
      volume = SILENCE
    if volume > maxvolume: maxvolume = volume
    a.queue.task_done()
    if time.time() >= time_update:
      scaled = (maxvolume-scale_min)/(scale_max-scale_min) * TARGET_HEIGHT
      scaled = min(scaled, 1.3*TARGET_HEIGHT, 254)
      if scaled < 0: scaled = 0
      command = "VD"
      for ch in range(TARGET_CHANNELS):
        vu_value[ch] = vu_value[ch] - DECAY * UPDATE_INTERVAL
        if vu_value[ch] < 0: vu_value[ch] = 0
        if scaled * random_gain[ch] > vu_value[ch]: vu_value[ch] = (1 - PULLUP) * vu_value[ch] + PULLUP * scaled * random_gain[ch]
        print int(vu_value[ch])*10*" "+ str(int(maxvolume*10)/10.0) + " dB"
        command += chr(int(vu_value[ch]))
      try: net.send(command)
      except socket.error: pass
      scale_window = scale_window[-scale_windowsize:] + [maxvolume]
      scale_min, scale_max = scale_min_max(scale_window)
      print "Scaling: ", int(scale_min*10)/10.0, int(scale_max*10)/10.0
      while time.time()>=time_update: time_update += UPDATE_INTERVAL
      maxvolume = SILENCE
    if time.time() >= time_random and TARGET_CHANNELS == 2:
      random_gain[0] = MAX_RANDOM_GAIN ** random.uniform(-1.0,1.0)
      random_gain[1] = 1 / random_gain[0]
      while time.time()>=time_random: time_random += RANDOMIZER_INTERVAL

