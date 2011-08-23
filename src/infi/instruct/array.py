from .base import Marshal, ConstReader, EMPTY_CONTEXT, MinMax, FixedSizer

class ArrayBase(object):
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "[ " + ", ".join([ self.element_marshal.to_repr(element, context) for element in obj ]) + " ]"

    def _approx_max_elements_by_size_bits(self):
        size_min_max = self.size_marshal.min_max_sizeof()
        return (1 << (size_min_max.max * 8)) - 1

    def min_max_sizeof(self):
        size_min_max = self.size_marshal.min_max_sizeof()
        element_min_max = self.element_marshal.min_max_sizeof()
        return MinMax(size_min_max.min,
                      size_min_max.max + self._approx_max_elements_by_size_bits() * element_min_max.max)

class VarSizeArrayMarshal(ArrayBase, Marshal):
    def __init__(self, size_marshal, element_marshal):
        super(VarSizeArrayMarshal, self).__init__()
        self.size_marshal = size_marshal
        self.element_marshal = element_marshal
    
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        size = self.size_marshal.create_from_stream(stream, context, *args, **kwargs)
        obj = []
        for i in xrange(size):
            obj.append(self.element_marshal.create_from_stream(stream, context, *args, **kwargs))
        return obj

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        self.size_marshal.write_to_stream(len(obj), stream, context)
        for element in obj:
            self.element_marshal.write_to_stream(element, stream, context)

    def sizeof(self, obj):
        return self.size_marshal.sizeof(len(obj)) + sum([ self.element_marshal.sizeof(element) for element in obj ])

class FixedSizeArrayMarshal(VarSizeArrayMarshal):
    def __init__(self, size, element_marshal):
        super(FixedSizeArrayMarshal, self).__init__(ConstReader(size), element_marshal)
        self.size = size
    
    def min_max_sizeof(self):
        element_min_max = self.element_marshal.min_max_sizeof()
        return MinMax(element_min_max.min * self.size, element_min_max.max * self.size)

class SumSizeArrayMarshal(ArrayBase, Marshal):
    def __init__(self, size_marshal, element_marshal):
        super(SumSizeArrayMarshal, self).__init__()
        self.size_marshal = size_marshal
        self.element_marshal = element_marshal
    
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = []
        total_bytes = self.size_marshal.create_from_stream(stream, context)
        has_tell = hasattr(stream, 'tell')
        while total_bytes > 0:
            element_size = stream.tell() if has_tell else 0
            element = self.element_marshal.create_from_stream(stream, context, *args, **kwargs)
            obj.append(element)
            element_size = stream.tell() - element_size if has_tell else self.element_marshal.sizeof(elemen)
            total_bytes -= element_size
        assert total_bytes == 0
        return obj

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        sum_size = sum([ self.element_marshal.sizeof(element) for element in obj ])
        self.size_marshal.write_to_stream(sum_size, stream, context)
        for element in obj:
            self.element_marshal.write_to_stream(element, stream, context)

    def sizeof(self, obj):
        sum_size = sum([ self.element_marshal.sizeof(element) for element in obj ])
        return self.size_marshal.sizeof(sum_size) + sum_size
