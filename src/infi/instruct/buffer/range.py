import operator
from .reference import Reference, NumericReference

class RangeFactory(object):
    def __getitem__(self, loc):
        return self._create_ranges(loc)

    def _create_ranges(self, loc):
        if isinstance(loc, (tuple, list)):
            return self.list_class([ self._create_ranges(loc_elem) for loc_elem in loc ])
        if isinstance(loc, slice):
            return self.slice_class(loc)
        if isinstance(loc, NumericReference):
            return self.numeric_class(loc)
        if isinstance(loc, (int, long)):
            return self.numeric_class(loc)
        raise TypeError("{0} is not a supported index type".format(repr(loc)))

class RangeReference(Reference):
    pass

class ListRangeReference(RangeReference):
    def __init__(self, l):
        # FIXME: check for mutual references in the elements?
        self.list = list(l)

    def value(self, obj):
        return reduce(operator.add, [ Reference.dereference(elem, obj) for elem in self.list ])

    def get_children(self):
        return self.list

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
        step = slic.step
        if step is not None:
            # TODO: if start/stop are immediates, we can test if they wrap around here.
            if step not in (1, -1):
                raise NotImplementedError("slice step must be None, 1 or -1 and not {0}".format(repr(step)))
        else:
            if slic.start is not None and slic.stop is not None:
                step = 1 if slic.start <= slic.stop else -1
            else:
                step = 1

        if Reference.mutual_reference(slic.start, slic.stop):
            raise CyclicReferenceError()

        self.slice = slice(slic.start, slic.stop, step)

    def value(self, obj):
        start = Reference.dereference(self.slice.start, obj)
        stop = Reference.dereference(self.slice.stop, obj)
        if start < 0 and stop > 0:
            raise ValueError("slices cannot wrap around (start < 0, end > 0) but got ({0}, {1})".format(start, stop))
        return [ slice(start, stop, self.slice.step) ]

    def get_children(self):
        return [ self.slice.start, self.slice.stop ]

class NumericRangeReference(RangeReference, NumericReference):
    def __init__(self, ref):
        self.ref = ref

    def value(self, obj):
        index = Reference.dereference(self.ref, obj)
        return [ slice(index, index + 1, 1) ]

    def get_children(self):
        return [ self.ref ]

# class BitRangeFactory(RangeFactory):
#     class list_class(ListRangeReference):
#         pass
#     class slice_class(SliceRangeReference):
#         pass
#     class numeric_class(NumericRangeReference):
#         pass

# class BitListRangeReference(ListRangeReference):
#     def __init__(self, byte_range_ref):
#         self.byte_range_ref = byte_range_ref

#     def value(self, obj):
#         # first, resolve the byte range.
#         byte_range = self.byte_range_ref.value(obj)

# class NestedBitRangeFactory(RangeFactory):
#     def __init__(self, byte_range):
#         self.byte_range = byte_range

#     def list_class(self, list):
#         pass

#     def slice_class(self, slice):
#         pass

#     def numeric_class(self, expr):
#         pass

class ByteRangeFactory(RangeFactory):
    class list_class(ListRangeReference):
        pass
    class slice_class(SliceRangeReference):
        pass
    class numeric_class(NumericRangeReference):
        pass
