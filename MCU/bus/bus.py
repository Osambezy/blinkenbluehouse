class Bus():

  def output(self, box_data_list):
    # box_data_list: [(box_addr, [(port_nr, maxval, val), ... ]), ... ]
    output = ''
    for box_data in box_data_list:
      output += frame(payload(box_data[1]), box_data[0])
    self.send(output)

# untere Ebene: Frames
def frame(data, address):
  START_SINGLE = '\x2A'
  START_MORE = '\x2B'
  CONT_END = '\xCC'
  CONT_MORE = '\xCD'
  DATABYTES = 7
  PADDING = '\xFF'
  def CHECKSUM(from_what):
    SALT = 85   # 01010101
    sum = 0
    for byte in from_what: sum = sum ^ ord(byte)
    return chr(sum ^ SALT)

  data += (7 - (len(data) % DATABYTES)) * PADDING
  frames = len(data) / DATABYTES

  output = ''
  for frame in range(frames):
    data_piece = data[frame*DATABYTES:(frame+1)*DATABYTES]
    if frame == 0:
      if frames == 1: frame_data = START_SINGLE + chr(address) + data_piece
      else: frame_data = START_MORE + chr(address) + data_piece
    else:
      if frame == frames-1: frame_data = CONT_END + chr(address) + data_piece
      else: frame_data = CONT_MORE + chr(address) + data_piece
    output += frame_data + CHECKSUM(frame_data)

  return output

# obere Ebene: Nutzdaten
def payload(data_list):
  """
  :Parameters:
    data_list : list
      format: [(port_num1, maxvalue1, value1), (port_num2, maxvalue2, value2), ...]
  """
  output = ''
  for data in data_list:
    if data[1] == 1:  # boolean
      ENCODING = 0
      if data[2] == 0: value = 0
      else: value = 1
    else:             # greyscale
      ENCODING = 1
      value = math.floor(255.0 * data[2] / data[1])
    output += chr((data[0] << 4) | ENCODING) + chr(value)
  return output


