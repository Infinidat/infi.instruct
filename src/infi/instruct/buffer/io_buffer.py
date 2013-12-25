import math
import collections


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
        # FIXME: On Python 2.7 there's no bytes() type (immutable byte sequence).
        if isinstance(buffer, (str, unicode)):
            self.buffer = bytearray(buffer)
        else:
            self.buffer = buffer
        self.start = start if start is not None else 0
        self.stop = stop if stop is not None else len(buffer)
        assert self.start >= 0
        assert self.stop <= len(buffer)
        assert self.start <= self.stop

    def __getitem__(self, key):
        start, stop = self._key_to_range(key)
        if isinstance(key, slice):
            return self._get_range(start, stop)
        else:  # must be int/float otherwise _key_to_range would raise an error
            return self._get_byte_bits(start, min(8, int((self.stop - start) * 8)))

    def __len__(self):
        return int(math.ceil(self.stop - self.start))

    def __iter__(self):
        for i in xrange(len(self)):
            yield self._get_byte_bits(i + self.start, min(int((self.stop - i - self.start) * 8), 8))

    def __str__(self):
        return str(bytearray(b for b in self))

    def __repr__(self):
        return "{0}(buffer={1!r}, start={2}, stop={3})".format(type(self), self.buffer, self.start, self.stop)

    def to_bitstr(self):
        result = []
        for i in xrange(int(self.start * 8), int(self.stop * 8)):
            byte_i, bit_i = float_to_byte_bit_pair(float(i) / 8)
            result.append((self.buffer[byte_i] >> bit_i) & 1)
        return "".join(str(n) for n in reversed(result))

    def to_bytearray(self):
        if int(self.start) == self.start:
            return self.buffer[int(self.start):int(math.ceil(self.stop))]
        else:
            return bytearray(list(self))  # very inefficient.

    def length(self):
        return self.stop - self.start

    def _get_range(self, start, stop):
        start_byte_ofs = int(start)
        stop_byte_ofs = int(math.ceil(stop))
        return type(self)(self.buffer[start_byte_ofs:stop_byte_ofs], start - start_byte_ofs, stop - start_byte_ofs)

    def _get_byte_bits(self, ofs, bit_len):
        # assert ofs >= 0 and bit_len >= 0, "ofs={0!r}, bit_len={1!r}".format(ofs, bit_len)
        byte_ofs, bit_ofs = float_to_byte_bit_pair(ofs)
        bit_mask = ((1 << bit_len) - 1)
        if bit_ofs == 0:
            return self.buffer[byte_ofs] & bit_mask
        elif bit_ofs < 0:
            bit_mask = ((1 << (bit_len + bit_ofs)) - 1)
            return self.buffer[0] & bit_mask
        elif bit_ofs + bit_len <= 8:
            return (self.buffer[byte_ofs] >> bit_ofs) & bit_mask
        else:
            cur_byte = self.buffer[byte_ofs]
            next_byte = self.buffer[byte_ofs + 1] if byte_ofs + 1 < len(self.buffer) else 0
            return (((cur_byte >> bit_ofs) & 0xFF) | ((next_byte << (8 - bit_ofs)) & 0xFF)) & bit_mask

    def _key_to_range(self, key):
        if isinstance(key, slice):
            if key.step not in (None, 1):
                raise NotImplementedError("step must be 1 or None")
            start = self._translate_offset(key.start if key.start is not None else 0)
            stop = self._translate_offset(key.stop if key.stop is not None else self.length())
            assert start <= stop and start >= 0, "start={0!r}, stop={1!r}".format(start, stop)
        elif isinstance(key, (float, int)):
            start = self._translate_offset(key)
            stop = start + 1
        else:
            raise TypeError("index must be int, float or a slice")
        return start, stop

    def _translate_offset(self, ofs):
        length = self.length()
        ofs = max(ofs + length, 0) if ofs < 0 else min(ofs, length)
        return ofs + self.start


class BitAwareByteArray(BitView, collections.MutableSequence):
    """
    Similar to BitView, but this class is mutable.
    """
    def __init__(self, source, start=0, stop=None):
        assert isinstance(source, bytearray)
        super(BitAwareByteArray, self).__init__(source, start, stop)

    def __setitem__(self, key, value):
        start, stop = self._key_to_range(key)
        value, value_len = self._value_to_value_and_length(value, stop - start)
        self._set_range(start, stop, value, value_len)

    def __delitem__(self, key):
        start, stop = self._key_to_range(key)
        self._del_range(start, stop)

    def insert(self, i, value):
        i = self._translate_offset(i)
        value, value_len = self._value_to_value_and_length(value)
        self._insert_zeros(i, i + value_len)
        self._copy_to_range(i, value, value_len)

    def extend(self, other):
        if isinstance(other, BitView):
            offset = self.stop
            self._insert_zeros(offset, offset + other.length())
            self._copy_to_range(offset, other, other.length())
        else:
            super(BitAwareByteArray, self).extend(other)

    def zfill(self, length):
        if length > self.length():
            self._insert_zeros(self.stop, self.stop + length - self.length())

    def __add__(self, other):
        if not isinstance(other, BitView):
            return NotImplemented
        copy = BitAwareByteArray(bytearray(self.buffer), start=self.start, stop=self.stop)
        copy.extend(other)
        return copy

    def __radd__(self, other):
        if not isinstance(other, BitView):
            return NotImplemented

        copy = BitAwareByteArray(bytearray(other.buffer), start=other.start, stop=other.stop)
        copy.extend(self)
        return copy

    def _set_range(self, start, stop, value, value_len):
        """
        Assumes that start and stop are already in 'buffer' coordinates. value is a byte iterable.
        value_len is fractional.
        """
        assert stop >= start and value_len >= 0
        range_len = stop - start
        if range_len < value_len:
            self._insert_zeros(stop, stop + value_len - range_len)
            self._copy_to_range(start, value, value_len)
        elif range_len > value_len:
            self._del_range(stop - (range_len - value_len), stop)
            self._copy_to_range(start, value, value_len)
        else:
            self._copy_to_range(start, value, value_len)

    def _copy_to_range(self, offset, iterable, iterable_len):
        remaining_bit_len = int(iterable_len * 8)
        for byte in iterable:
            self._set_byte_bits(offset, min(remaining_bit_len, 8), byte)
            offset += 1
            remaining_bit_len -= 8

    def _del_range(self, start, stop):
        assert stop >= start
        start_byte, stop_byte = int(math.ceil(start)), int(math.floor(stop))
        whole_byte_delta = stop_byte - start_byte

        # If we can remove whole bytes from the buffer, we'll do that first.
        if whole_byte_delta >= 1:
            del self.buffer[start_byte:stop_byte]
            self.stop -= whole_byte_delta
            stop -= whole_byte_delta

        # Here we have at most 8 bits to remove, so we need to "shift" the entire array.
        if stop > start:
            ofs = start
            bit_len_frac = stop - start
            while (ofs + bit_len_frac) < self.stop:
                self._set_byte_bits(ofs, 8, self._get_byte_bits(ofs + bit_len_frac, 8))
                ofs += 1
            self.stop -= bit_len_frac
            if int(math.ceil(self.stop)) < len(self.buffer):
                del self.buffer[-1]

    def _insert_zeros(self, start, stop):
        assert start >= 0 and start <= stop, "start={0!r}, stop={1!r}".format(start, stop)
        assert start <= self.stop
        start_byte, stop_byte = int(math.ceil(start)), int(math.floor(stop))
        whole_byte_delta = stop_byte - start_byte

        # If we can insert whole bytes to the buffer, we'll do that first.
        if whole_byte_delta >= 1:
            self.buffer[start_byte:start_byte] = bytearray(whole_byte_delta)
            self.stop += whole_byte_delta
            stop -= whole_byte_delta

        if stop > start:
            assert stop - start <= 2, "start={0}, stop={1}".format(start, stop)
            bit_len_frac = stop - start
            while int(math.ceil(self.stop + bit_len_frac)) > len(self.buffer):
                self.buffer.append(0)

            if start < self.stop:
                # Inserting in the middle, so we copy from end to start.
                ofs = self.stop + bit_len_frac - 1
                while ofs >= start:
                    self._set_byte_bits(ofs, 8, self._get_byte_bits(ofs - bit_len_frac, 8))
                    ofs -= 1
            self.stop += bit_len_frac

    def _set_byte_bits(self, ofs, bit_len, value):
        byte_ofs, bit_ofs = float_to_byte_bit_pair(ofs)
        if bit_ofs == 0 and bit_len == 8:
            self.buffer[byte_ofs] = value  # shortcut
        elif (bit_ofs + bit_len) <= 8:
            self.buffer[byte_ofs] &= ~(((1 << bit_len) - 1) << bit_ofs)
            self.buffer[byte_ofs] |= (value << bit_ofs) & 0xFF
        else:
            first_byte_bit_len = 8 - bit_ofs
            self._set_byte_bits(ofs, first_byte_bit_len, value & ((1 << first_byte_bit_len) - 1))
            self._set_byte_bits(byte_ofs + 1, bit_len - first_byte_bit_len, value >> first_byte_bit_len)

    def _value_to_value_and_length(self, value, int_value_len=1):
        value_len = 0
        if isinstance(value, BitView):
            value_len = value.length()
        elif isinstance(value, collections.Sized):
            value_len = len(value)
        elif isinstance(value, collections.Iterable):
            value = bytearray(value)
            value_len = len(value)
        elif isinstance(value, int):
            # Short circuit: make bit ranges accept int values by their bit length.
            bit_length = max(1, value.bit_length())
            if bit_length > int_value_len * 8:
                # Safety measure for short circuit: if user is assigning an int with more bits than the range of
                # bits that he specified we shout.
                raise ValueError("trying to assign int {0} with bit length {1} to bit length {2}".format(value,
                                 bit_length, int(int_value_len * 8)))
            l = []
            for n in range(0, bit_length, 8):
                l.append(value % 256)
                value /= 256
            value = l
            value_len = max(float(bit_length) / 8, int_value_len)
        else:
            raise TypeError("value must be iterable or int")
        return value, value_len


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
            result = self.buffer[range.start:range.stop]
        else:
            result = BitAwareByteArray(bytearray())
            for range in range_list:
                assert not range.is_open()
                result += self.buffer[range.start:range.stop]

        return result

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
        value_start = 0

        for range in range_list:
            assert not range.is_open()
            assert range.start >= 0 and range.start <= range.stop
            if range.byte_length() > len(value) - value_start:
                raise ValueError("trying to assign a value with smaller length than the range it's given")
            self.buffer.zfill(range.start)
            self.buffer[range.start:range.stop] = value[value_start:value_start + range.byte_length()]
            value_start += range.byte_length()

    def get(self):
        return self.buffer
