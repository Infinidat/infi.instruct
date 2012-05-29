class InputBuffer(object):
    # TODO validate that there are no overlapping fields
    def __init__(self, buffer):
        self.buffer = buffer

    def get(self, position):
        result = bytearray()
        for range in position:
            result += self.buffer[range]
        return result

class OutputBuffer(object):
    # TODO validate that there are no overlapping fields
    def __init__(self):
        self.buffer = bytearray()
        self.relative_values = []

    def set(self, value, position):
        for range in position:
            if self._is_relative_range(range):
                self.relative_values.append((range, value))
            else:
                range, value = self._make_range_and_value_positive(range, value)
                value_len = range.stop - range.start
                if value_len != len(value):
                    raise ValueError("trying to assign block with size {0} to range {1}".format(len(value),
                                                                                                value_len))
                # if the start of this range is beyond the current length of our buffer, we pad our buffer with zeros.
                self.buffer = self.buffer.zfill(range.start)
                self.buffer[range] = value

    def get(self):
        if len(self.relative_values) > 0:
            for range, value in self.relative_values:
                if range.start is not None:
                    if range.start >= 0:
                        self.buffer = self.buffer.zfill(range.start)
                        self.buffer[range] = value
                    else:
                        self.buffer = self.buffer.zfill(abs(range.start))
                        self.buffer[range] = value
            self.relative_values = []
        return self.buffer

    def _is_relative_range(self, range):
        return range.start is None or range.stop is None or range.start < 0 or range.stop < 0

    def _make_range_and_value_positive(self, range, value):
        if range.step == 1:
            return range, value
        else:
            assert range.step == -1 and range.start >= range.stop
            return slice(range.stop, range.start, 1), reversed(value)
