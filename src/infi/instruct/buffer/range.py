import sys
import operator
import functools

from .reference import Reference, NumericReference

@functools.total_ordering
class SequentialRange(object):
    """
    An almost slice-like object representing a sequential (continous) range from start to stop (exclusive).
    This class can only work on non-negative values, but allows stop to be None (open-ended).
    """
    def __init__(self, start, stop):
        self.start = start if start is not None else 0
        self.stop = stop

        assert self.start >= 0
        if self.stop is not None:
            assert self.stop >= 0
            assert self.start <= self.stop

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
        return self.start < other.start and self.to_absolute(sys.maxint).stop < other.to_absolute(sys.maxint).stop

    def __repr__(self):
        return "SequentialRange(start={0!r}, stop={1!r})".format(self.start, self.stop)

    def overlaps(self, other):
        self_imag_stop = self.to_absolute(sys.maxint)
        other_imag_stop = other.to_absolute(sys.maxint)

        return (self.start <= other.start and self_imag_stop >= other.start) or \
            (self.start <= other_imag_stop and self_imag_stop >= other_imag_stop)

    @classmethod
    def list_sum_length(cls, range_list):
        sum = 0
        for n in [ range.length() for range in range_list ]:
            if n is None:
                return None
            sum += n
        return sum

    @classmethod
    def list_max_stop(cls, range_list):
        m = 0
        for range in range_list:
            if range.is_open():
                return None
            m = max(m, range.stop)
        return m

    @classmethod
    def list_overlaps(cls, range_list):
        if len(range_list) <= 1:
            return False

        range_list = sorted(range_list)
        for i in xrange(0, len(range_list) - 1):
            if range_list[i].overlaps(range_list[i + 1]):
                return True
        return False

class RangeReference(Reference):
    pass

class ListRangeReference(RangeReference):
    def __init__(self, l):
        self.list = [ Reference.to_ref(obj) for obj in l ]

    def evaluate(self, ctx):
        return reduce(operator.add, [ ref(ctx) for ref in self.list ])

    def __add__(self, other):
        if isinstance(other, ListRangeReference):
            return ListRangeReference(self.list + other.list)
        elif isinstance(other, RangeReference):
            return ListRangeReference(self.list + [ other ])
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, ListRangeReference):
            return ListRangeReference(other.list + self.list)
        elif isinstance(other, RangeReference):
            return ListRangeReference( [ other ] + self.list)
        return NotImplemented

class SliceRangeReference(RangeReference):
    def __init__(self, slic):
        assert slic.step in (1, None)
        assert slic.start is None or slic.start >= 0
        assert slic.stop is None or slic.stop >= 0
        assert (slic.start is None or slic.stop is None) or (slic.start <= slic.stop)

        self.start = Reference.to_ref(slic.start)
        self.stop = Reference.to_ref(slic.stop)

    def evaluate(self, ctx):
        return [ SequentialRange(self.start(ctx), self.stop(ctx)) ]

    def __repr__(self):
        return "[{0!r}:{1!r}]".format(self.start, self.stop)

class NumericRangeReference(RangeReference, NumericReference):
    def __init__(self, ref):
        assert ref >= 0
        self.ref = Reference.to_ref(ref)

    def evaluate(self, ctx):
        index = self.ref(ctx)
        assert index >= 0
        return [ SequentialRange(index, index + 1) ]

class RangeFactory(object):
    def __getitem__(self, loc):
        return self._create_ranges(loc)

    def _create_ranges(self, loc):
        if isinstance(loc, (tuple, list)):
            return ListRangeReference([ self._create_ranges(loc_elem) for loc_elem in loc ])
        if isinstance(loc, slice):
            return SliceRangeReference(loc)
        if isinstance(loc, (NumericReference, int, long)):
            return NumericRangeReference(loc)
        raise TypeError("{0} is not a supported index type".format(repr(loc)))
