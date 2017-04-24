import re
import argparse

from bitarray import bitarray

MAX_PAYLOAD_LENGTH = 2096

class BluetoothAddress:
    def __init__(self, LAP, UAP, NAP):
        #Lower Address Part
        self.LAP = LAP
        #Upper Address Part
        self.UAP = UAP
        #Non-Significant Address Part
        self.NAP = NAP

class Packet:
    def __init__(self, stream):
        self.device_address = BluetoothAddress('100000010000000000000000', 0, 0)
        self.access_code = self.generate_access_code()
        # Header bits
        self.LT_ADDR = bitarray('000') # 3 Bit Transport address
        self.TYPE = bitarray('0000') # 4 Bit Packet Type
        self.FLOW = '1' # 1 bit FLOW control
        self.ARQN = '1' # 1 bit acknowledgment
        self.SEQN = '1' # 1 bit sequential numbering scheme
        self.HEC = bitarray('00000000') # 8 bit header error check
        self.payload = stream

    @property
    def header(self):
        header = bitarray()
        header.extend(self.LT_ADDR)
        header.extend(self.TYPE)
        header.extend(self.FLOW)
        header.extend(self.ARQN)
        header.extend(self.SEQN)
        header.extend(self.HEC)
        return header


    def generate_access_code(self):
	# Psuedo random sequence given by bluetooth spec docs
        rand_seq = bitarray('0011111100101010001100111101110101101001101100010010000111000001')

        access_code = bitarray()

        info_seq = bitarray(endian='little')
        info_seq.extend(self.device_address.LAP)

        if MSB(info_seq):
            info_seq.extend('110010')
        else:
            info_seq.extend('001101')

        # Generate the Sync Word by XORing the
        # information sequence with the 30 LSB
        # of the psuedo random sequence. Then
        # XOR that with the entire PN sequence
        sync_word = bitarray(34)
        sync_word.setall(False)
        sync_word.extend(rand_seq[34:] ^ info_seq)
        sync_word = sync_word ^ rand_seq

        # Add trailer
        if MSB(sync_word):
            sync_word.extend('0101')
        else:
            sync_word.extend('1010')

        # Add preample
        if LSB(sync_word):
            access_code.extend('1010')
        else:
            access_code.extend('0101')
        access_code.extend(sync_word)

        return access_code

    def __str__(self):
        string = (str(self.access_code) + str(self.header) + str(self.payload)).replace('bitarray(\'', '')
        string = string.replace('\')', '')
        return string

def MSB(bits):
    endian = bits.endian()
    if endian == 'little':
        return bits[-1]
    else:
        return bits[0]

def LSB(bits):
    endian = bits.endian()
    if endian == 'little':
        return bits[0]
    else:
        return bits[-1]

parser = argparse.ArgumentParser(description="Redtooth Packet Generation")
parser.add_argument('-i', '--input', help='Input data')
parser.add_argument('-o', '--output', help='Output File')
args = parser.parse_args()

stream = bitarray(endian='little')

with open(args.input, 'r') as f:
    data = f.readlines()
    for d in data:
        stream.frombytes(d.encode())

with open(args.output, 'w') as f:
    while stream.length() > 0:
        data = stream[0:MAX_PAYLOAD_LENGTH]
        packet = Packet(data)
        del stream[0:MAX_PAYLOAD_LENGTH]
        f.write(str(packet) + '\n')
