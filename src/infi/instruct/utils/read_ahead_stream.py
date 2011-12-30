class ReadAheadStream(object):
    def __init__(self, stream):
        self.buffer = ''
        self.stream = stream
        self.read_ahead_mode = False

    def set_read_ahead(self, mode):
        self.read_ahead_mode = mode

    def is_read_ahead_empty(self):
        return len(self.buffer) == 0
        
    def read(self, size):
        assert size >= 0

        res = ''
        if self.read_ahead_mode:
            res += self.stream.read(size)
            self.buffer += res
        else:
            if len(self.buffer) > 0:
                buffer_bytes_to_read = min(len(self.buffer), size)
                res = self.buffer[0:buffer_bytes_to_read]
                self.buffer = self.buffer[buffer_bytes_to_read:]
            if len(res) < size:
                res += self.stream.read(size - len(res))
        return res
    
    def write(self, buf):
        if len(self.buffer) > 0:
            raise IOError("cannot write while there are still bytes in the read-ahead buffer")
        if self.read_ahead:
            raise IOError("cannot write while in read-ahead mode")
        return self.stream.write(buf)
