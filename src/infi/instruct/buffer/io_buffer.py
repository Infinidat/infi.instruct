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
        else: # must be int/float otherwise _key_to_range would raise an error
            return self._get_byte_bits(start, 8)

    def __len__(self):
        return int(math.ceil(self.stop - self.start))

    def __iter__(self):
        for i in xrange(len(self)):
            yield self._get_byte_bits(i + self.start, min(int((self.stop - i - self.start) * 8), 8))

    def __str__(self):
        return str(bytearray(b for b in self))

    def __repr__(self):
        return "{0}(buffer={1!r}, start={2}, stop={3})".format(type(self), self.buffer, self.start, self.stop)

    def length(self):
        return self.stop - self.start

    def _get_range(self, start, stop):
        start_byte_ofs = int(start)
        stop_byte_ofs = int(math.ceil(stop))
        return type(self)(self.buffer[start_byte_ofs:stop_byte_ofs], start - start_byte_ofs, stop - start_byte_ofs)

    def _get_byte_bits(self, ofs, bit_len):
        byte_ofs, bit_ofs = float_to_byte_bit_pair(ofs)
        bit_mask = ((1 << bit_len) - 1)
        if bit_ofs == 0:
            return self.buffer[byte_ofs] & bit_mask
        elif bit_ofs + bit_len <= 8:
            return (self.buffer[byte_ofs] >> bit_ofs) & bit_mask
        else:
            next_byte = self.buffer[byte_ofs + 1] if byte_ofs + 1 < len(self.buffer) else 0
            return (((self.buffer[byte_ofs] >> bit_ofs) & 0xFF) | ((next_byte << (8 - bit_ofs)) & 0xFF)) &  bit_mask

    def _key_to_range(self, key):
        if isinstance(key, slice):
            if key.step not in (None, 1):
                raise NotImplementedError("step must be 1 or None")
            start = self._translate_offset(key.start if key.start is not None else 0)
            stop = self._translate_offset(key.stop if key.stop is not None else self.length())
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
        if not isinstance(other, BitView):
            return super(BitAwareByteArray, self).extend(other)
        offset = self.stop
        self._insert_zeros(offset, offset + other.length())
        self._copy_to_range(offset, other, other.length())

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
        assert stop >= start
        start_byte, stop_byte = int(math.ceil(start)), int(math.floor(stop))
        whole_byte_delta = stop_byte - start_byte

        # If we can insert whole bytes to the buffer, we'll do that first.
        if whole_byte_delta >= 1:
            self.buffer[start_byte:start_byte] = bytearray(whole_byte_delta)
            self.stop += whole_byte_delta
            stop -= whole_byte_delta

        if stop > start:
            bit_len_frac = stop - start
            if int(math.ceil(self.stop + bit_len_frac)) > len(self.buffer):
                self.buffer.append(0)
            ofs = self.stop + bit_len_frac - 1
            while ofs >= start:
                self._set_byte_bits(ofs, 8, self._get_byte_bits(ofs - bit_len_frac, 8))
                ofs -= 1
            self.stop += bit_len_frac

    def _set_byte_bits(self, ofs, bit_len, value):
        byte_ofs, bit_ofs = float_to_byte_bit_pair(ofs)
        if bit_ofs == 0 and bit_len == 8:
            self.buffer[byte_ofs] = value # shortcut
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
            # Short circuit: make bit ranges accept int values if their len <= 8
            value_len = min(1, int_value_len)
            if value.bit_length() > value_len * 8:
                # Safety measure for short circuit: if user is assigning an int with more bits than the range of
                # bits that he specified we shout.
                raise ValueError("trying to assign int {0} to bit length {1}".format(value, value_len))
            value = [ value ]
        else:
            raise TypeError("value must be iterable or int")
        return value, value_len

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
