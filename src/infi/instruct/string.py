from infi.pyutils.mixin import install_mixin_if

from .base import Sizer, ApproxSizer, FixedSizer, AllocatingReader, Writer, ReprCapable, EMPTY_CONTEXT
from .base import UNBOUNDED_MIN_MAX, is_sizer, is_approx_sizer
from .errors import InstructError, InvalidValueError

PADDING_DIRECTION_NONE  = 0
PADDING_DIRECTION_RIGHT = 1
PADDING_DIRECTION_LEFT  = 2
PADDING_DIRECTION_BOTH  = 3

def _strip(obj, dir, padding):
    if dir == PADDING_DIRECTION_NONE:
        return obj
    elif dir == PADDING_DIRECTION_RIGHT:
        return obj.rstrip(padding)
    elif dir == PADDING_DIRECTION_LEFT:
        return obj.lstrip(padding)
    else:
        return obj.strip(padding)

def _pad(obj, size, dir, padding):
    pad_len = size - len(obj)
    if pad_len < 0:
        raise InvalidValueError("fixed-size item length is expected to be of length %d or smaller but instead got %d (item=%s)" % (size, len(obj), repr(obj)))
    elif pad_len == 0:
        return obj
    
    if dir == PADDING_DIRECTION_RIGHT or dir == PADDING_DIRECTION_BOTH:
        return obj + padding[0] * pad_len
    elif dir == PADDING_DIRECTION_LEFT:
        return (padding[0] * pad_len) + obj
    else:
        # PADDING_DIRECTION_NONE
        raise InvalidValueError("no padding specified but item length %d is smaller than required length %d (item=%s)" %
                                (len(obj), size, obj))

class PaddedStringIO(FixedSizer, AllocatingReader, Writer, ReprCapable):
    def __init__(self, size, padding='\x00', padding_direction=PADDING_DIRECTION_RIGHT):
        super(PaddedStringIO, self).__init__()
        self.size = size
        self.padding = padding
        self.padding_direction = padding_direction
    
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return _strip(stream.read(self.size), self.padding_direction, self.padding)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(_pad(obj, self.size, self.padding_direction, self.padding))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

class VarSizeStringIO(AllocatingReader, Writer, ReprCapable):
    class MySizer(Sizer):
        def sizeof(self, obj, context=EMPTY_CONTEXT):
            return self.size_io.sizeof(obj) + len(obj)

    class MyApproxSizer(ApproxSizer):
        def min_max_sizeof(self, context=EMPTY_CONTEXT):
            return self.size_io.min_max_sizeof() + UNBOUNDED_MIN_MAX
    
    def __init__(self, size_io, padding='\x00', padding_direction=PADDING_DIRECTION_RIGHT):
        super(VarSizeStringIO, self).__init__()
        self.size_io = size_io
        self.padding = padding
        self.padding_direction = padding_direction
        install_mixin_if(self, VarSizeStringIO.MySizer, is_sizer(self.size_io))
        install_mixin_if(self, VarSizeStringIO.MyApproxSizer, is_approx_sizer(self.size_io))

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        buffer_len = self.size_io.create_from_stream(stream, context)
        obj = stream.read(buffer_len)
        if len(obj) < buffer_len:
            raise InstructError("Expected to read %d bytes from stream but read only %d" % (buffer_len, len(obj)))
        return _strip(obj, self.padding_direction, self.padding)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stripped_obj = _strip(obj, self.padding_direction, self.padding)
        self.size_io.write_to_stream(len(stripped_obj), stream, context)
        stream.write(stripped_obj)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

class FixedSizeBufferIO(PaddedStringIO):
    def __init__(self, size):
        super(FixedSizeBufferIO, self).__init__(size, padding='', padding_direction=PADDING_DIRECTION_NONE)

class VarSizeBufferIO(VarSizeStringIO):
    def __init__(self, size_io):
        super(VarSizeBufferIO, self).__init__(size_io, padding='', padding_direction=PADDING_DIRECTION_NONE)
