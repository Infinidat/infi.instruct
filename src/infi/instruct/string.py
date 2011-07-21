from .base import Sizer, ApproxSizer, FixedSizer, AllocatingReader, Writer, ReprCapable, EMPTY_CONTEXT
from .base import UNBOUNDED_MIN_MAX, is_sizer, is_approx_sizer
from .mixin import install_mixin_if
from .errors import InstructError, InvalidValueError

class PaddedStringIO(FixedSizer, AllocatingReader, Writer, ReprCapable):
    def __init__(self, size, padding='\x00'):
        super(PaddedStringIO, self).__init__()
        self.size = size
        self.padding = padding
        assert len(self.padding) == 1
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = stream.read(self.size)
        return obj.rstrip(self.padding)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        if len(obj) > self.size:
            raise InvalidValueError("fixed-size string length is expected to be of length %d or smaller but instead got %d (string=%s)" % (self.size, len(obj), repr(obj)))
        stream.write(obj)
        if len(obj) < self.size:
            stream.write(self.padding * (self.size - len(obj)))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

class FixedSizeBufferIO(FixedSizer, AllocatingReader, Writer, ReprCapable):
    def __init__(self, size):
        super(FixedSizeBufferIO, self).__init__()
        self.size = size
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return stream.read(self.size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        if len(obj) != self.size:
            raise InvalidValueError("fixed-size buffer length is expected to be of length %d but instead got %d (buffer=%s)" % (self.size, len(obj), repr(obj)))
        stream.write(obj)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

class VarSizeBufferIO(AllocatingReader, Writer, ReprCapable):
    def __init__(self, size_io):
        super(VarSizeBufferIO, self).__init__()
        self.size_io = size_io
        install_mixin_if(self, Sizer, is_sizer(self.size_io))
        install_mixin_if(self, ApproxSizer, is_approx_sizer(self.size_io))

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        buffer_len = self.size_io.create_from_stream(stream, context)
        obj = stream.read(buffer_len)
        if len(obj) < buffer_len:
            raise InstructError("Expected to read %d bytes from stream but read only %d" % (buffer_len, len(obj)))
        return obj

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        self.size_io.write_to_stream(len(obj), stream, context)
        stream.write(obj)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

    # Conditional implementations (added only if sizer is a Sizer/ApproxSizer)
    def _Sizer_sizeof(self, obj, context=EMPTY_CONTEXT):
        return self.size_io.sizeof(obj) + len(obj)

    def _ApproxSizer_min_max_sizeof(self, context=EMPTY_CONTEXT):
        return self.size_io.min_max_sizeof().add(UNBOUNDED_MIN_MAX)
