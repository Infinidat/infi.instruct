import struct
import types
from infi.exceptools import chain

from .base import FixedSizer, AllocatingReader, Writer, ReprCapable, EMPTY_CONTEXT
from .errors import InstructError, NotEnoughDataError

class NumericIO(FixedSizer, AllocatingReader, Writer, ReprCapable):
    def __init__(self, format_string, type):
        super(NumericIO, self).__init__()
        self.format_string = format_string
        self.type = type
        self.size = struct.calcsize(format_string)

    def create_from_stream(self, stream, context=EMPTY_CONTEXT):
        packed_value = stream.read(self.size)
        if len(packed_value) < self.size:
            raise NotEnoughDataError(expected=self.size, actually_read=len(packed_value))
        try:
            return struct.unpack(self.format_string, packed_value)[0]
        except struct.error, e:
            raise chain(InstructError("Unpacking error occurred"))

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        try:
            stream.write(struct.pack(self.format_string, obj))
        except struct.error, e:
            raise chain(InstructError("Packing error occurred"))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        if self.type in (types.IntType, types.LongType):
            return context.get('int_repr_format', '%d') % obj
        elif self.type == types.FloatType:
            return context.get('float_repr_format', '%f') % obj
        return repr(obj)

"""unsigned, big endian 8-bit integer"""
UBInt8IO = NumericIO(">B", types.IntType)
"""unsigned, big endian 16-bit integer"""
UBInt16IO = NumericIO(">H", types.IntType)
"""unsigned, big endian 32-bit integer"""
UBInt32IO = NumericIO(">L", types.IntType)
"""unsigned, big endian 64-bit integer"""
UBInt64IO = NumericIO(">Q", types.LongType)
"""signed, big endian 8-bit integer"""
SBInt8IO = NumericIO(">b", types.IntType)
"""signed, big endian 16-bit integer"""
SBInt16IO = NumericIO(">h", types.IntType)
"""signed, big endian 32-bit integer"""
SBInt32IO = NumericIO(">l", types.IntType)
"""signed, big endian 64-bit integer"""
SBInt64IO = NumericIO(">q", types.IntType)
"""unsigned, little endian 8-bit integer"""
ULInt8IO = NumericIO("<B", types.IntType)
"""unsigned, little endian 16-bit integer"""
ULInt16IO = NumericIO("<H", types.IntType)
"""unsigned, little endian 32-bit integer"""
ULInt32IO = NumericIO("<L", types.IntType)
"""unsigned, little endian 64-bit integer"""
ULInt64IO = NumericIO("<Q", types.LongType)
"""signed, little endian 8-bit integer"""
SLInt8IO = NumericIO("<b", types.IntType)
"""signed, little endian 16-bit integer"""
SLInt16IO = NumericIO("<h", types.IntType)
"""signed, little endian 32-bit integer"""
SLInt32IO = NumericIO("<l", types.IntType)
"""signed, little endian 64-bit integer"""
SLInt64IO = NumericIO("<q", types.LongType)
"""unsigned, native endianity 8-bit integer"""
UNInt8IO = NumericIO("=B", types.IntType)
"""unsigned, native endianity 16-bit integer"""
UNInt16IO = NumericIO("=H", types.IntType)
"""unsigned, native endianity 32-bit integer"""
UNInt32IO = NumericIO("=L", types.IntType)
"""unsigned, native endianity 64-bit integer"""
UNInt64IO = NumericIO("=Q", types.LongType)
"""signed, native endianity 8-bit integer"""
SNInt8IO = NumericIO("=b", types.IntType)
"""signed, native endianity 16-bit integer"""
SNInt16IO = NumericIO("=h", types.IntType)
"""signed, native endianity 32-bit integer"""
SNInt32IO = NumericIO("=l", types.IntType)
"""signed, native endianity 64-bit integer"""
SNInt64IO = NumericIO("=q", types.LongType)
"""big endian, 32-bit IEEE floating point number"""
BFloat32IO = NumericIO(">f", types.FloatType)
"""little endian, 32-bit IEEE floating point number"""
LFloat32IO = NumericIO("<f", types.FloatType)
"""native endianity, 32-bit IEEE floating point number"""
NFloat32IO = NumericIO("=f", types.FloatType)
"""big endian, 64-bit IEEE floating point number"""
BFloat64IO = NumericIO(">d", types.FloatType)
"""little endian, 64-bit IEEE floating point number"""
LFloat64IO = NumericIO("<d", types.FloatType)
"""native endianity, 64-bit IEEE floating point number"""
NFloat64IO = NumericIO("=d", types.FloatType)
