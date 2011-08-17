from .base import Marshal, ConstReader, FixedSizer, EMPTY_CONTEXT, MinMax
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

class VarSizeStringMarshal(Marshal):
    def __init__(self, size_marshal, padding='\x00', padding_direction=PADDING_DIRECTION_RIGHT):
        super(VarSizeStringMarshal, self).__init__()
        self.size_marshal = size_marshal
        self.padding = padding
        self.padding_direction = padding_direction

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        buffer_len = self.size_marshal.create_from_stream(stream, context)
        obj = stream.read(buffer_len)
        if len(obj) < buffer_len:
            raise InstructError("Expected to read %d bytes from stream but read only %d" % (buffer_len, len(obj)))
        return _strip(obj, self.padding_direction, self.padding)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stripped_obj = _strip(obj, self.padding_direction, self.padding)
        self.size_marshal.write_to_stream(len(stripped_obj), stream, context)
        stream.write(stripped_obj)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

    def sizeof(self, obj):
        return self.size_marshal.sizeof(obj) + len(_strip(obj, self.padding_direction, self.padding))

    def min_max_sizeof(self):
        size_min_max = self.size_marshal.min_max_sizeof()
        return MinMax(size_min_max.min, size_min_max.max + (1 << (size_min_max.max * 8)) - 1)

class PaddedStringMarshal(FixedSizer, VarSizeStringMarshal):
    def __init__(self, size, padding='\x00', padding_direction=PADDING_DIRECTION_RIGHT):
        super(PaddedStringMarshal, self).__init__(ConstReader(size), padding, padding_direction)
        self.size = size

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stripped_obj = _strip(obj, self.padding_direction, self.padding)
        stream.write(stripped_obj)
        if len(stripped_obj) < self.size:
            stream.write(self.padding[0] * (self.size - len(stripped_obj)))

class VarSizeBufferMarshal(VarSizeStringMarshal):
    def __init__(self, size_marshal):
        super(VarSizeBufferMarshal, self).__init__(size_marshal, padding='', padding_direction=PADDING_DIRECTION_NONE)

class FixedSizeBufferMarshal(PaddedStringMarshal):
    def __init__(self, size):
        super(FixedSizeBufferMarshal, self).__init__(size, padding='', padding_direction=PADDING_DIRECTION_NONE)
