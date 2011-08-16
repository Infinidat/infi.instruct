from infi.pyutils.mixin import install_mixin_if

from .base import AllocatingReader, Writer, ReprCapable, EMPTY_CONTEXT
from .base import MinMax, Sizer, ApproxSizer, is_sizer, is_approx_sizer

class FixedSizeArrayIO(AllocatingReader, Writer, ReprCapable):
    class MySizer(Sizer):
        def sizeof(self, obj, context=EMPTY_CONTEXT):
            return sum([ self.element_io.sizeof(element, context) for element in obj ])

    class MyApproxSizer(ApproxSizer):
        def min_max_sizeof(self, context=EMPTY_CONTEXT):
            min_max = self.element_io.min_max_sizeof(context)
            return MinMax(min_max.min * self.size, min_max.max * self.size)
        
    def __init__(self, size, element_io):
        super(FixedSizeArrayIO, self).__init__()
        self.size = size
        self.element_io = element_io
        install_mixin_if(self, FixedSizeArrayIO.MySizer, is_sizer(self.element_io))
        install_mixin_if(self, FixedSizeArrayIO.MyApproxSizer, is_approx_sizer(self.element_io))
    
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = []
        for i in xrange(self.size):
            obj.append(self.element_io.create_from_stream(stream, context, *args, **kwargs))
        return obj

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        assert len(obj) == self.size
        for element in obj:
            self.element_io.write_to_stream(element, stream, context)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "[ " + ", ".join([ self.element_io.to_repr(element, context) for element in obj ]) + " ]"

class SumSizeArrayIO(AllocatingReader, Writer, ReprCapable):
    class MySizer(Sizer):
        def sizeof(self, obj, context=EMPTY_CONTEXT):
            sum_size = sum([ self.element_io.sizeof(element, context) for element in obj ])
            return sum([ self.element_io.sizeof(element, context) for element in obj ], self.size_io.sizeof(sum_size))

    class MyApproxSizer(ApproxSizer):
        def min_max_sizeof(self, context=EMPTY_CONTEXT):
            size_min_max = self.size_io.min_max_sizeof(context)
            # Theoretically, if we know the upper limit of the size field (e.g. max elements), we can multiply this by
            # the max element size and get a number that's less than maxint. But for our purposes it's enough to do
            # this:
            return MinMax(size_min_max.min)
        
    def __init__(self, size_io, element_io):
        super(SumSizeArrayIO, self).__init__()
        self.size_io = size_io
        self.element_io = element_io

        assert is_sizer(element_io)
        install_mixin_if(self, SumSizeArrayIO.MySizer, is_sizer(self.element_io) and is_sizer(self.size_io))
        install_mixin_if(self, SumSizeArrayIO.MyApproxSizer, is_approx_sizer(self.size_io))
    
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = []
        total_bytes = self.size_io.create_from_stream(stream, context)
        while total_bytes > 0:
            element = self.element_io.create_from_stream(stream, context, *args, **kwargs)
            obj.append(element)
            total_bytes -= self.element_io.sizeof(element, context)
        assert total_bytes == 0
        return obj

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        sum_size = sum([ self.element_io.sizeof(element, context) for element in obj ])
        self.size_io.write_to_stream(sum_size, stream, context)
        for element in obj:
            self.element_io.write_to_stream(element, stream, context)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "[ " + ", ".join([ self.element_io.to_repr(element, context) for element in obj ]) + " ]"
