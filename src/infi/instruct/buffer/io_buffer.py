import math
import collections
from bitstring import Bits, BitArray
from .._compat import is_string_or_bytes, range, PY2
from six import integer_types


def float_to_byte_bit_pair(n):
    return (int(n), int((n - int(n)) * 8))


class BitView(collections.Sequence):
    """
    Provides bit indexing over an existing buffer.

    For example, you can do this:
    bit_view = BitView(...)
    bits_2_and_3 = bit_view[0.125 * 2:0.125 * 4]

    Basically, you can access the buffer with 1/8 fractions.
    """
    def __init__(self, buffer, start=0, stop=None):
        super(BitView, self).__init__()
        start = int(start * 8) if start is not None else 0
        if stop is None:
            stop = buffer.length if isinstance(buffer, Bits) else len(buffer) * 8
        else:
            stop = int(stop * 8)

        assert start >= 0 and stop >= 0
        assert start <= stop
        # FIXME: On Python 2.7 there's no bytes() type (immutable byte sequence).
        if is_string_or_bytes(buffer) or isinstance(buffer, bytearray):
            assert stop <= len(buffer) * 8
            self.buffer = BitArray(bytes=buffer, offset=start, length=stop - start)
        elif isinstance(buffer, BitView):
            self.buffer = buffer.buffer[start:stop]
        elif isinstance(buffer, Bits):
            self.buffer = BitArray(buffer[start:stop])
        elif isinstance(buffer, BitArray):
            self.buffer = buffer[start:stop]
        elif isinstance(buffer, (collections.Sized, collections.Iterable)):
            self.buffer = BitArray(bytearray(buffer))
        else:
            raise TypeError("buffer is not Bits/BitArray - instead it's {}".format(type(buffer)))

    def __getitem__(self, key):
        start, stop = self._key_to_range(key)
        if isinstance(key, slice):
            return type(self)(self.buffer[start:stop])
        else:  # must be int/float otherwise _key_to_range would raise an error
            return self._get_byte_bits(start, 8)

    def __len__(self):
        return (self.buffer.length + 7) / 8

    def __iter__(self):
        for i in range(len(self)):
            yield self._get_byte_bits(int(i * 8), 8)

    def __str__(self):
        if PY2:
            return self.to_bytes()
        else:
            raise NotImplementedError("BitViews should not be treated as strings in Python 3. Use to_bytes instead")

    def __repr__(self):
        return "{0}(buffer={1!r})".format(type(self), self.buffer)

    def to_bitstr(self):
        return self.buffer.bin

    def to_bytearray(self):
        return bytearray(self.buffer.tobytes())

    def to_bytes(self):        
        return self.buffer.tobytes()

    def length(self):
        return self.buffer.length / 8.0

    def _get_byte_bits(self, bit_ofs, bit_len):
        return ord(self.buffer[bit_ofs:bit_ofs + bit_len].tobytes()[0])

    def _key_to_range(self, key):
        if isinstance(key, slice):
            if key.step not in (None, 1):
                raise NotImplementedError("step must be 1 or None")
            start = int(key.start * 8) if key.start is not None else None
            stop = int(key.stop * 8) if key.stop is not None else None
        elif isinstance(key, integer_types + (float,)):
            start = int(key * 8)
            stop = start + 8
        else:
            raise TypeError("index must be int, float or a slice")
        return start, stop


class BitAwareByteArray(BitView, collections.MutableSequence):
    """
    Similar to BitView, but this class is mutable.
    """
    def __init__(self, source, start=0, stop=None):
        super(BitAwareByteArray, self).__init__(source, start, stop)

    def __setitem__(self, key, value):
        start, stop = self._key_to_range(key)
        value = self._value_to_bitview(value)
        self.buffer[start:stop] = value[0:(stop - start) / 8.0].buffer

    def __delitem__(self, key):
        start, stop = self._key_to_range(key)
        self.buffer[start:stop] = None

    def insert(self, i, value):
        value = self._value_to_bitview(value)
        ofs = int(i * 8)
        if ofs > self.buffer.length:
            self.buffer[self.buffer.length:ofs + value.length] = 0
        self.buffer[ofs:ofs + value.length] = value

    def extend(self, other):
        other = self._value_to_bitview(other)
        self.buffer.append(other.buffer)

    def zfill(self, length):
        n = int(length * 8) - self.buffer.length
        if n > 0:
            self.buffer[self.buffer.length:self.buffer.length + n] = 0

    def __add__(self, other):
        if not isinstance(other, BitView):
            return NotImplemented
        return BitAwareByteArray(self.buffer + other.buffer)

    def __radd__(self, other):
        if not isinstance(other, BitView):
            return NotImplemented
        return BitAwareByteArray(other.buffer + self.buffer)

    def _value_to_bitview(self, value):
        if isinstance(value, BitView):
            return value
        elif isinstance(value, Bits):
            return BitView(value)
        elif isinstance(value, (collections.Sized, collections.Iterable)):
            return BitView(bytearray(value))
        # elif isinstance(value, integer_types):
        #     # Short circuit: make bit ranges accept int values by their bit length.
        #     bit_length = max(1, value.bit_length())
        #     if bit_length > int_value_len * 8:
        #         # Safety measure for short circuit: if user is assigning an int with more bits than the range of
        #         # bits that he specified we shout.
        #         raise ValueError("trying to assign int {0} with bit length {1} to bit length {2}".format(value,
        #                          bit_length, int(int_value_len * 8)))
        #     l = []
        #     for n in range(0, bit_length, 8):
        #         l.append(value % 256)
        #         value //= 256
        #     value = l
        #     value_len = max(float(bit_length) / 8, int_value_len)
        raise TypeError("value must be iterable or int and not {}".format(type(value)))


class InputBuffer(object):
    def __init__(self, buffer):
        if isinstance(buffer, BitView):
            self.buffer = buffer
        else:
            self.buffer = BitView(buffer)

    def get(self, range_list):
        if len(range_list) == 1:
            # Shortcut: if it's a simple range we can just return a subset of the bit view.
            range = range_list[0]
            assert not range.is_open()
            return self.buffer[range.start:range.stop]
        else:
            result = BitArray()
            for range in range_list:
                assert not range.is_open()
                result.append(self.buffer.buffer[int(range.start * 8):int(range.stop * 8)])
            return BitAwareByteArray(result)

    def length(self):
        return len(self.buffer)

    def __repr__(self):
        return "InputBuffer({0!r})".format(self.buffer)


class OutputBuffer(object):
    def __init__(self, buffer=None):
        if isinstance(buffer, BitAwareByteArray):
            self.buffer = buffer
        elif isinstance(buffer, bytearray):
            self.buffer = BitAwareByteArray(buffer)
        elif buffer is None:
            self.buffer = BitAwareByteArray(bytearray())
        else:
            raise TypeError("buffer must be either BitAwareByteArray, bytearray or None but instead is {0}".
                            format(type(buffer)))

    def set(self, value, range_list):
        value = BitView(value)
        ofs = 0
        for range in range_list:
            assert not range.is_open()
            assert range.start >= 0 and range.start <= range.stop
            self.buffer.zfill(range.start)
            if range.byte_length() + ofs > value.length():
                raise ValueError("trying to assign a value with smaller length than the range it's given (value={!r} range={})".format(value, range))
            self.buffer[range.start:range.stop] = value[ofs:range.byte_length() + ofs]
            ofs += range.byte_length()

    def to_bytearray(self):
        return self.buffer.to_bytearray()
