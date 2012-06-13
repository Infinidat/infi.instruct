import sys
import operator
import functools

from .reference import Reference, NumericReference

BIT = 0.125

@functools.total_ordering
class SequentialRange(object):
    """
    An almost slice-like object representing a sequential (continous) range from start to stop (exclusive).
    This class can only work on non-negative values, but allows stop to be None (open-ended).
    """
    def __init__(self, start, stop):
        self.start = start if start is not None else 0
        self.stop = stop

        assert self.start >= 0, "start={0!r}".format(self.start)
        if self.stop is not None:
            assert self.stop >= 0, "stop={0!r}".format(self.stop)
            assert self.start <= self.stop, "start={0!r}, stop={1!r}".format(self.start, self.stop)

    def is_open(self):
        """Returns True if the range is open, i.e. stop is None"""
        return self.stop is None

    def to_closed(self, total_len):
        """Converts a potentially open range into a closed range by making stop a finite value (total_len)."""
        assert total_len >= self.start
        return SequentialRange(self.start, self.stop if self.stop is not None else total_len)

    def length(self):
        if self.is_open():
            return None
        return self.stop - self.start

    def to_slice(self):
        return slice(self.start, self.stop, 1)

    def __eq__(self, other):
        return self.start == other.start and self.stop == other.stop

    def __lt__(self, other):
        return self.start < other.start and self.to_closed(sys.maxint).stop < other.to_closed(sys.maxint).stop

    def __repr__(self):
        return "SequentialRange(start={0!r}, stop={1!r})".format(self.start, self.stop)

    def overlaps(self, other):
        a, b = (self, other)  if self.start <= other.start else (other, self)
        a_imag_stop = a.to_closed(sys.maxint).stop
        return a_imag_stop > b.start

    def contains(self, point):
        return self.start <= point and (self.stop is None or self.stop > point)

class SequentialRangeList(list):
    def byte_length(self):
        sum = 0
        for r in self:
            if r.is_open():
                return None
            sum += r.length()
        return sum

    def has_overlaps(self):
        sorted_list = sorted(self)
        for i in xrange(0, len(sorted_list) - 1):
            if sorted_list[i].overlaps(sorted_list[i + 1]):
                return True
        return False

    def max_stop(self):
        m = 0
        for r in self:
            if r.is_open():
                return None
            m = max(m, r.stop)
        return m

    def is_open(self):
        return any(r.is_open() for r in self)

    def to_closed(self, total_len):
        return SequentialRangeList(r.to_closed(total_len) for r in self)

    def find_container(self, point):
        for r in self:
            if r.contains(point):
                return r
        return None

    def find_relative_container_index(self, point):
        sum_length = 0
        for i in xrange(len(self)):
            if self[i].is_open() or ((point - sum_length - self[i].length()) <= 0):
                return i, sum_length
            sum_length += self[i].length()
        return None

    def __add__(self, other):
        return SequentialRangeList(super(SequentialRangeList, self).__add__(other))

    def __radd__(self, other):
        return SequentialRangeList(super(SequentialRangeList, self).__radd__(other))

class RangeReference(Reference):
    def __add__(self, other):
        me = self.list if isinstance(self, ListRangeReference) else [ self ]
        if isinstance(other, ListRangeReference):
            return ListRangeReference(me + other.list)
        elif isinstance(other, RangeReference):
            return ListRangeReference(me + [ other ])
        return NotImplemented

    def __radd__(self, other):
        me = self.list if isinstance(self, ListRangeReference) else [ self ]
        if isinstance(other, ListRangeReference):
            return ListRangeReference(other.list + me)
        elif isinstance(other, Reference):
            return ListRangeReference( [ other ] + me)
        return NotImplemented

class ListRangeReference(RangeReference):
    def __init__(self, l):
        super(ListRangeReference, self).__init__()
        self.list = [ Reference.to_ref(obj) for obj in l ]

    def evaluate(self, ctx):
        return SequentialRangeList(reduce(operator.add, [ ref(ctx) for ref in self.list ]))

class BitContainer(object):
    def __init__(self):
        self.bits = BitRangeFactory(self)

class ByteListRangeReference(BitContainer, ListRangeReference):
    def __init__(self, l):
        BitContainer.__init__(self)
        ListRangeReference.__init__(self, l)

class ByteSliceRangeReference(BitContainer, RangeReference):
    def __init__(self, slic):
        assert slic.step in (1, None)
        assert slic.start is None or slic.start >= 0
        assert slic.stop is None or slic.stop >= 0
        assert (slic.start is None or slic.stop is None) or (slic.start <= slic.stop)

        BitContainer.__init__(self)
        RangeReference.__init__(self)

        self.start = Reference.to_ref(slic.start)
        self.stop = Reference.to_ref(slic.stop)

    def evaluate(self, ctx):
        return SequentialRangeList([ SequentialRange(self.start(ctx), self.stop(ctx)) ])

    def __repr__(self):
        return "[{0!r}:{1!r}]".format(self.start, self.stop)

class ByteNumericRangeReference(BitContainer, RangeReference):
    def __init__(self, ref):
        assert ref >= 0
        super(ByteNumericRangeReference, self).__init__()
        self.ref = Reference.to_ref(ref)

    def evaluate(self, ctx):
        index = self.ref(ctx)
        assert index >= 0
        return SequentialRangeList([ SequentialRange(index, index + 1) ])

class ByteRangeFactory(object):
    def __getitem__(self, loc):
        if isinstance(loc, (tuple, list)):
            return ByteListRangeReference([ self.__getitem__(loc_elem) for loc_elem in loc ])
        if isinstance(loc, slice):
            return ByteSliceRangeReference(loc)
        if isinstance(loc, (NumericReference, int, long)):
            return ByteNumericRangeReference(loc)
        raise TypeError("{0} is not a supported index type".format(repr(loc)))

class BitRangeReference(RangeReference):
    def __init__(self, parent_range_ref):
        super(BitRangeReference, self).__init__()
        self.parent_range_ref = parent_range_ref

class BitNumericRangeReference(BitRangeReference):
    def __init__(self, parent_range_ref, ref):
        super(BitNumericRangeReference, self).__init__(parent_range_ref)
        self.ref = Reference.to_ref(ref)

    def evaluate(self, ctx):
        range_list = self.parent_range_ref(ctx)
        assert len(range_list) >= 1

        byte_offset = float(self.ref(ctx)) / 8
        assert byte_offset >= 0

        i, sum_length = range_list.find_relative_container_index(byte_offset)
        if i is None:
            raise ValueError("Bit offset {0} is out of range for range sequence {1!r}".format(self.ref(ctx),
                                                                                              range_list))
        return SequentialRangeList([ SequentialRange(byte_offset - sum_length + range_list[i].start,
                                                     byte_offset - sum_length + range_list[i].start + BIT) ])

class BitSliceRangeReference(BitRangeReference):
    def __init__(self, parent_range_ref, slic):
        assert slic.step in (1, None)
        assert slic.start is None or slic.start >= 0
        assert slic.stop is None or slic.stop >= 0
        assert (slic.start is None or slic.stop is None) or (slic.start <= slic.stop)

        super(BitSliceRangeReference, self).__init__(parent_range_ref)
        self.start = Reference.to_ref(slic.start)
        self.stop = Reference.to_ref(slic.stop)

    def __repr__(self):
        return "{0!r}.bits[{1}:{2}]".format(self.parent_range_ref, self.start, self.stop)

    def evaluate(self, ctx):
        range_list = self.parent_range_ref(ctx)
        assert len(range_list) >= 1

        bit_range = SequentialRange(float(self.start(ctx)) / 8, float(self.stop(ctx)) / 8)

        i, sum_length = range_list.find_relative_container_index(bit_range.start)
        if i is None:
            raise ValueError("Bit offset {0} is out of range for range sequence {1!r}".format(
                int(bit_range.start * 8), range_list))

        if bit_range.is_open():
            subrange_start = range_list[i].start + bit_range.start - sum_length
            return SequentialRangeList([ SequentialRange(subrange_start, range_list[i].stop) ] + range_list[i + 1:])

        bit_range_remaining_len = bit_range.length()
        result = []
        for i in xrange(i, len(range_list)):
            r = range_list[i]
            subrange_start = r.start + bit_range.start - sum_length
            if r.is_open() or (r.stop - subrange_start) >= bit_range_remaining_len:
                subrange_stop = subrange_start + bit_range_remaining_len
            else:
                subrange_stop = r.stop

            result.append(SequentialRange(subrange_start, subrange_stop))

            bit_range_remaining_len -= (subrange_stop - subrange_start)
            if bit_range_remaining_len == 0:
                break

        if bit_range_remaining_len > 0:
            raise ValueError("Bit range {0!r} is out of range for parent range {1!r}".format(bit_range, range_list))

        return SequentialRangeList(result)

class BitRangeFactory(object):
    def __init__(self, parent_range_ref):
        self.parent_range_ref = parent_range_ref

    def __getitem__(self, loc):
        if isinstance(loc, (tuple, list)):
            return ListRangeReference([ self.__getitem__(loc_elem) for loc_elem in loc ])
        if isinstance(loc, slice):
            return BitSliceRangeReference(self.parent_range_ref, loc)
        if isinstance(loc, (NumericReference, int, long)):
            return BitNumericRangeReference(self.parent_range_ref, loc)
        raise TypeError("{0} is not a supported index type".format(repr(loc)))
