def packet_bool(data, width, height):
    out_data = ''
    for byte in data:
        out_data += byte
    # 4x magic, 2x height, 2x width, 2x channels, 2x maxval, data
    packet = '\x23\x54\x26\x66' + chr(height // 256) + chr(height % 256) + \
        chr(width // 256) + chr(width % 256) + '\x00\x01\x00\x01' + out_data
    return packet


def packet_alloff(width, height):
    packet = '\x23\x54\x26\x66' + chr(height // 256) + chr(height % 256) + \
        chr(width // 256) + chr(width % 256) + '\x00\x01\x00\x01' + \
        width * height * '\x00'
    return packet


def packet_allon(width, height):
    packet = '\x23\x54\x26\x66' + chr(height // 256) + chr(height % 256) + \
        chr(width // 256) + chr(width % 256) + '\x00\x01\x00\x01' + \
        width * height * '\x01'
    return packet
