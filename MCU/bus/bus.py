import time

START_SINGLE = '\x2A'
START_MORE = '\x2B'
CONT_END = '\xCC'
CONT_MORE = '\xCD'
DATABYTES = 7
PADDING = '\xFF'


class Bus():

    def output(self, box_data_list):
        """Send data to the bus for multiple receivers.

        Arguments:
        box_data_list -- [(box_addr, [(port_nr, maxval, val), ... ]), ... ]
        """
        output = ''
        for box_data in box_data_list:
            output = frame(payload(box_data[1]), box_data[0])
            self.send(output)


def frame(data, address):
    """Generate one or more BBH bus frames for the given data payload.

    This is the outer layer of the BBH bus protocol as specified in the
    protocol documentation.  Depending on the length of the data payload, one
    or more frames with according start bytes are generated.  Frames are padded
    if necessary and checksums are added.
    The result is returned as a string and can be directly sent to the bus.

    Arguments:
    data -- the data payload to be sent
    address -- receiver address (box number)
    """
    data += (7 - (len(data) % DATABYTES)) * PADDING
    frames = len(data) / DATABYTES
    output = ''
    for frame in range(frames):
        data_piece = data[frame * DATABYTES:(frame + 1) * DATABYTES]
        if frame == 0:
            if frames == 1:
                frame_data = START_SINGLE + chr(address) + data_piece
            else:
                frame_data = START_MORE + chr(address) + data_piece
        else:
            if frame == frames - 1:
                frame_data = CONT_END + chr(address) + data_piece
            else:
                frame_data = CONT_MORE + chr(address) + data_piece
        output += frame_data + frame_checksum(frame_data)
    return output


def frame_checksum(frame_data):
    sum = 3
    for byte in frame_data:
        sum = (sum + ord(byte)) % 256
    return chr(sum)


def payload(data_list):
    """Generate bus data payload from light data.

    This is the inner layer of the BBH bus protocol as specified in the
    protocol documentation.  The data payload for a single box is generated
    from a list of multiple ports (light outputs) on this box.

    Arguments:
    data_list -- [(port_num1, channels1, maxvalue1, data1),
                  (port_num2, channels2, maxvalue2, data2), ...]
    """
    output = ''
    for data in data_list:
        if len(data[3]) != data[1]:
            raise ValueError("wrong length of output data")
        if data[1] == 1 and data[2] == 1:
            ENCODING = 0      # boolean
        elif data[1] == 1 and data[2] == 255:
            ENCODING = 1      # greyscale
        elif data[1] == 3 and data[2] == 255:
            ENCODING = 2      # rgb
        else:
            raise ValueError("unsupported bus output parameters")
        output += chr((data[0] << 4) | ENCODING) + data[3]
    return output
