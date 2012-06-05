class InputBuffer(object):
    def __init__(self, buffer):
        self.buffer = buffer

    def get(self, range_list):
        result = bytearray()
        for range in range_list:
            assert not range.is_open()
            result += self.buffer[range.start:range.stop]
        return result

    def length(self):
        return len(self.buffer)

class OutputBuffer(object):
    def __init__(self):
        self.buffer = bytearray()

    def set(self, value, range_list):
        value_start = 0
        for range in range_list:
            assert not range.is_open()
            if range.length() > len(value) - value_start:
                raise ValueError("trying to assign a value with smaller length than the range it's given")
            self.buffer = self.buffer.zfill(range.start)
            self.buffer[range.start:range.stop] = value[value_start:value_start + range.length()]
            value_start += range.length()

    def get(self):
        return self.buffer
