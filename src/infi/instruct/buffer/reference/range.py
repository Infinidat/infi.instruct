import operator

from infi.instruct.utils.safe_repr import safe_repr
from infi.instruct.buffer.range import BIT, SequentialRange, SequentialRangeList

from .reference import Reference

class RangeReference(Reference):
    def __init__(self):
        super(RangeReference, self).__init__(False)

    def __add__(self, other):
        me = self.list if isinstance(self, ListRangeReference) else [self]
        if isinstance(other, ListRangeReference):
            return ListRangeReference(me + other.list)
        elif isinstance(other, RangeReference):
            return ListRangeReference(me + [other])
        return NotImplemented

    def __radd__(self, other):
        me = self.list if isinstance(self, ListRangeReference) else [self]
        if isinstance(other, ListRangeReference):
            return ListRangeReference(other.list + me)
        elif isinstance(other, Reference):
            return ListRangeReference([other] + me)
        return NotImplemented


class ListRangeReference(RangeReference):
    def __init__(self, l):
        super(ListRangeReference, self).__init__()
        self.list = [Reference.to_ref(obj) for obj in l]

    def evaluate(self, ctx):
        return SequentialRangeList(reduce(operator.add, [ref.deref(ctx) for ref in self.list]))

    def __safe_repr__(self):
        return "[{0}]".format(", ".join(safe_repr(o for o in self.list)))


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
        assert slic.start is None or Reference.is_numeric_ref(slic.start) or slic.start >= 0
        assert slic.stop is None or Reference.is_numeric_ref(slic.stop) or slic.stop >= 0
        assert ((slic.start is None or slic.stop is None)
                or Reference.is_numeric_ref(slic.start)
                or Reference.is_numeric_ref(slic.stop)
                or (slic.start <= slic.stop))

        BitContainer.__init__(self)
        RangeReference.__init__(self)

        self.start = Reference.to_ref(slic.start)
        self.stop = Reference.to_ref(slic.stop)

    def evaluate(self, ctx):
        return SequentialRangeList([SequentialRange(self.start.deref(ctx), self.stop.deref(ctx))])

    def __safe_repr__(self):
        return "[{0}:{1}]".format(safe_repr(self.start), safe_repr(self.stop))


class ByteNumericRangeReference(BitContainer, RangeReference):
    def __init__(self, ref):
        assert Reference.is_numeric_ref(ref) or ref >= 0
        super(ByteNumericRangeReference, self).__init__()
        self.ref = Reference.to_ref(ref)

    def evaluate(self, ctx):
        index = self.ref.deref(ctx)
        assert index >= 0
        return SequentialRangeList([SequentialRange(index, index + 1)])

    def __safe_repr__(self):
        return safe_repr(self.ref)


class ByteRangeFactory(object):
    def __getitem__(self, loc):
        if isinstance(loc, (tuple, list)):
            return ByteListRangeReference([self.__getitem__(loc_elem) for loc_elem in loc])
        if isinstance(loc, slice):
            return ByteSliceRangeReference(loc)
        if isinstance(loc, (int, long)) or (isinstance(loc, Reference) and loc.is_numeric()):
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
        range_list = self.parent_range_ref.deref(ctx)
        assert len(range_list) >= 1

        byte_offset = float(self.ref.deref(ctx)) / 8
        assert byte_offset >= 0

        i, sum_length = range_list.find_relative_container_index(byte_offset)
        if i is None:
            raise ValueError("Bit offset {0} is out of range for range sequence {1!r}".format(self.ref.deref(ctx),
                                                                                              range_list))
        return SequentialRangeList([SequentialRange(byte_offset - sum_length + range_list[i].start,
                                                    byte_offset - sum_length + range_list[i].start + BIT)])

    def __safe_repr__(self):
        return "{0}.bits[{1}]".format(safe_repr(self.parent_range_ref), safe_repr(self.ref))


class BitSliceRangeReference(BitRangeReference):
    def __init__(self, parent_range_ref, slic):
        assert slic.step in (1, None)
        assert slic.start is None or slic.start >= 0
        assert slic.stop is None or slic.stop >= 0
        assert (slic.start is None or slic.stop is None) or (slic.start <= slic.stop)

        super(BitSliceRangeReference, self).__init__(parent_range_ref)
        self.start = Reference.to_ref(slic.start)
        self.stop = Reference.to_ref(slic.stop)

    def evaluate(self, ctx):
        range_list = self.parent_range_ref.deref(ctx)
        assert len(range_list) >= 1

        bit_range = SequentialRange(float(self.start.deref(ctx)) / 8, float(self.stop.deref(ctx)) / 8)

        i, sum_length = range_list.find_relative_container_index(bit_range.start)
        if i is None:
            raise ValueError("Bit offset {0} is out of range for range sequence {1!r}".format(
                int(bit_range.start * 8), range_list))

        if bit_range.is_open():
            subrange_start = range_list[i].start + bit_range.start - sum_length
            return SequentialRangeList([SequentialRange(subrange_start, range_list[i].stop)] + range_list[i + 1:])

        bit_range_remaining_len = bit_range.byte_length()
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

    def __safe_repr__(self):
        return "{0}.bits[{1}:{2}]".format(safe_repr(self.parent_range_ref), safe_repr(self.start), safe_repr(self.stop))


class BitRangeFactory(object):
    def __init__(self, parent_range_ref):
        self.parent_range_ref = parent_range_ref

    def __getitem__(self, loc):
        if isinstance(loc, (tuple, list)):
            return ListRangeReference([self.__getitem__(loc_elem) for loc_elem in loc])
        if isinstance(loc, slice):
            return BitSliceRangeReference(self.parent_range_ref, loc)
        if isinstance(loc, (int, long)) or (isinstance(loc, Reference) and loc.is_numeric()):
            return BitNumericRangeReference(self.parent_range_ref, loc)
        raise TypeError("{0} is not a supported index type".format(repr(loc)))
