import sys
import functools

BIT = 0.125


class SequentialRangeMixin(object):
    """Common interface between SquentialRange and SequentialRangeList"""

    def is_open(self):
        pass

    def to_closed(self, new_stop):
        pass

    def byte_length(self):
        pass

    def max_stop(self):
        pass


@functools.total_ordering
class SequentialRange(SequentialRangeMixin):
    """
    An almost slice-like object representing a sequential (continuous) range from start to stop (exclusive).
    This class can only work on non-negative values, but allows stop to be None (open-ended).
    """
    def __init__(self, start, stop):
        """
        :param start: range start (non-negative)
        :type start: int or float
        :param stop: range stop (can be None for open range). If not None, must be >= start.
        :type stop: int, float or None
        """
        self.start = start if start is not None else 0
        self.stop = stop

        assert self.start >= 0, "start={0!r}".format(self.start)
        if self.stop is not None:
            assert self.stop >= 0, "stop={0!r}".format(self.stop)
            assert self.start <= self.stop, "start={0!r}, stop={1!r}".format(self.start, self.stop)

    def is_open(self):
        """
        :returns: True if the range is open, i.e. stop is None
        :rtype: bool
        """
        return self.stop is None

    def to_closed(self, new_stop):
        """
        :param new_stop: new stop value to use if existing stop is None. Must be >= start.
        :type new_stop: int or float
        :returns: new closed range, using the current stop if self is a closed range or new_stop if self is open.
        :rtype: SequentialRange
        """
        assert new_stop >= self.start, "self.start ({0}) is bigger than new_stop ({1})".format(self.start, new_stop)
        return SequentialRange(self.start, self.stop if self.stop is not None else new_stop)

    def byte_length(self):
        """
        :returns: length of range if a closed range or None if open range.
        :rtype: int or float or None
        """
        if self.is_open():
            return None
        return self.stop - self.start

    def max_stop(self):
        """
        :returns: length of range if a closed range or None if open range.
        :rtype: int or float or None
        """
        return self.stop

    def to_slice(self):
        """
        :returns: a slice object from start to stop
        :rtype: slice
        """
        return slice(self.start, self.stop, 1)

    def overlaps(self, other):
        """
        :returns: True if there's an overlap (non-empty intersection) between two ranges
        :rtype: bool
        """
        a, b = (self, other) if self.start <= other.start else (other, self)
        a_imag_stop = a.to_closed(sys.maxint).stop
        return a_imag_stop > b.start

    def contains(self, point):
        """
        :param point: point to check if contained in range
        :type point: int or float
        :returns: True if the range contains `point`
        :rtype: bool
        """
        return self.start <= point and (self.stop is None or self.stop > point)

    def __eq__(self, other):
        return self.start == other.start and self.stop == other.stop

    def __lt__(self, other):
        return self.start < other.start and self.to_closed(sys.maxint).stop < other.to_closed(sys.maxint).stop

    def __repr__(self):
        return "SequentialRange(start={0!r}, stop={1!r})".format(self.start, self.stop)


class SequentialRangeList(list, SequentialRangeMixin):
    """
    List of SquentialRange objects that contains some utility methods and range arithmetics.
    """

    def is_open(self):
        return any(r.is_open() for r in self)

    def to_closed(self, total_len):
        return SequentialRangeList(r.to_closed(total_len) for r in self)

    def byte_length(self):
        """
        :returns: sum of lengthes of all ranges or None if one of the ranges is open
        :rtype: int, float or None
        """
        sum = 0
        for r in self:
            if r.is_open():
                return None
            sum += r.byte_length()
        return sum

    def has_overlaps(self):
        """
        :returns: True if one or more range in the list overlaps with another
        :rtype: bool
        """
        sorted_list = sorted(self)
        for i in xrange(0, len(sorted_list) - 1):
            if sorted_list[i].overlaps(sorted_list[i + 1]):
                return True
        return False

    def max_stop(self):
        """
        :returns: maximum stop in list or None if there's at least one open range
        :type: int, float or None
        """
        m = 0
        for r in self:
            if r.is_open():
                return None
            m = max(m, r.stop)
        return m

    def sorted(self):
        """
        :returns: a new sorted SequentialRangeList
        :rtype: SequentialRangeList
        """
        return SequentialRangeList(sorted(self))

    def byte_offset(self, bytes):
        """
        Maps `bytes` length to a sequence's offset. For example, if we do byte_offset(5) and our list of sequences is
        [(0, 2), (10, 11), (40, 45)] then the returned value will be 42.
        Note that `bytes` must be <= byte_length().
        :returns: actual offset in one of the sequences in the range for request byte length.
        :rtype: int or float
        """
        remaining_bytes = bytes
        for r in self:
            if r.is_open() or r.byte_length() >= remaining_bytes:
                return r.start + remaining_bytes
            else:
                remaining_bytes -= r.byte_length()
        assert False, "requested byte offset {0!r} is outside the range list {1!r}".format(bytes, self)

    def find_relative_container_index(self, point):
        sum_length = 0
        for i in xrange(len(self)):
            if self[i].is_open() or ((point - sum_length - self[i].byte_length()) <= 0):
                return i, sum_length
            sum_length += self[i].byte_length()
        return None

    def __add__(self, other):
        return SequentialRangeList(super(SequentialRangeList, self).__add__(other))

    def __radd__(self, other):
        return SequentialRangeList(super(SequentialRangeList, self).__radd__(other))
