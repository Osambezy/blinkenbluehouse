class Bus():

  def output(self, box_data_list):
    # box_data_list: [(box_addr, [(port_nr, maxval, val), ... ]), ... ]
    output = ''
    for box_data in box_data_list:
      output += frame(payload(box_data[1]), box_data[0])
    self.send(output)

# lower layer: frames
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

# upper layer: light data
def payload(data_list):
  """
  :Parameters:
    data_list : list
      format: [(port_num1, channels1, maxvalue1, data1), (port_num2, channels2, maxvalue2, data2), ...]
  """
  output = ''
  for data in data_list:
    if len(data[3]) != data[1]: raise ValueError, "wrong length of output data"
    if data[1] == 1 and data[2] == 1:
      ENCODING = 0      # boolean
    elif data[1] == 1 and data[2] == 255:
      ENCODING = 1      # greyscale
    elif data[1] == 3 and data[2] == 255:
      ENCODING = 2      # rgb
    else: raise ValueError, "unsupported bus output parameters"
    output += chr((data[0] << 4) | ENCODING) + data[3]
  return output


