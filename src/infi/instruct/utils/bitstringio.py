class BitStringIO(object):
    """
    Naive bit stream implementation.
    """
    def __init__(self, byte_size_or_array):
        self.position = 0
        self.value = bytearray(byte_size_or_array)

    def getvalue(self):
        return str(self.value)

    def write(self, value, bits_to_write):
        if (bits_to_write + self.position) > len(self.value) * 8:
            raise IOError("attempting to write past the end of the buffer")

        byte_i, bit_i = (self.position / 8, self.position % 8)

        bits_written = 0
        if bit_i != 0:
            chunk_to_write = min(8 - bit_i, bits_to_write)
            bitmask = (1 << chunk_to_write) - 1
            self.value[byte_i] |= (value & bitmask) << bit_i
            byte_i += 1
            bits_written = chunk_to_write

        for n in xrange(bits_written, bits_to_write, 8):
            chunk_to_write = min(8, bits_to_write - n)
            bitmask = (1 << chunk_to_write) - 1
            self.value[byte_i] |= (value >> n) & bitmask
            byte_i += 1
        
        self.position += bits_to_write

    def read(self, bits_to_read):
        if len(self.value) * 8 < (bits_to_read + self.position):
            raise IOError("attempting to read past the end of the buffer")
        
        byte_i, bit_i = (self.position / 8, self.position % 8)
        result = 0
        bits_read = 0

        if bit_i != 0:
            chunk_to_read = min(8 - bit_i, bits_to_read)
            bitmask = (1 << chunk_to_read) - 1
            result = (self.value[byte_i] >> bit_i) & bitmask
            bits_read = chunk_to_read
            byte_i += 1

        for n in xrange(bits_read, bits_to_read, 8):
            chunk_to_read = min(8, bits_to_read - n)
            bitmask = (1 << chunk_to_read) - 1
            result |= (self.value[byte_i] & bitmask) << n
            byte_i += 1

        self.position += bits_to_read
        return result

    def seek(self, position):
        self.position = position
        assert self.position >= 0 and ((self.position / 8) < len(self.value))
