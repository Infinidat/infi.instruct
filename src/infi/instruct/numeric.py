from __future__ import absolute_import

import struct
import types
from infi.exceptools import chain

from .base import FixedSizer, Marshal, EMPTY_CONTEXT
from .errors import InstructError, NotEnoughDataError

class NumericMarshal(FixedSizer, Marshal):
    """
    Numeric fields template class. Using Python's ``struct`` package it serializes and deserializes numeric fields with
    different endianity and bit size.
    """
    def __init__(self, format_string, type):
        super(NumericMarshal, self).__init__()
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
UBInt8Marshal = NumericMarshal(">B", types.IntType)
"""unsigned, big endian 16-bit integer"""
UBInt16Marshal = NumericMarshal(">H", types.IntType)
"""unsigned, big endian 32-bit integer"""
UBInt32Marshal = NumericMarshal(">L", types.IntType)
"""unsigned, big endian 64-bit integer"""
UBInt64Marshal = NumericMarshal(">Q", types.LongType)
"""signed, big endian 8-bit integer"""
SBInt8Marshal = NumericMarshal(">b", types.IntType)
"""signed, big endian 16-bit integer"""
SBInt16Marshal = NumericMarshal(">h", types.IntType)
"""signed, big endian 32-bit integer"""
SBInt32Marshal = NumericMarshal(">l", types.IntType)
"""signed, big endian 64-bit integer"""
SBInt64Marshal = NumericMarshal(">q", types.IntType)
"""unsigned, little endian 8-bit integer"""
ULInt8Marshal = NumericMarshal("<B", types.IntType)
"""unsigned, little endian 16-bit integer"""
ULInt16Marshal = NumericMarshal("<H", types.IntType)
"""unsigned, little endian 32-bit integer"""
ULInt32Marshal = NumericMarshal("<L", types.IntType)
"""unsigned, little endian 64-bit integer"""
ULInt64Marshal = NumericMarshal("<Q", types.LongType)
"""signed, little endian 8-bit integer"""
SLInt8Marshal = NumericMarshal("<b", types.IntType)
"""signed, little endian 16-bit integer"""
SLInt16Marshal = NumericMarshal("<h", types.IntType)
"""signed, little endian 32-bit integer"""
SLInt32Marshal = NumericMarshal("<l", types.IntType)
"""signed, little endian 64-bit integer"""
SLInt64Marshal = NumericMarshal("<q", types.LongType)
"""unsigned, native endianity 8-bit integer"""
UNInt8Marshal = NumericMarshal("=B", types.IntType)
"""unsigned, native endianity 16-bit integer"""
UNInt16Marshal = NumericMarshal("=H", types.IntType)
"""unsigned, native endianity 32-bit integer"""
UNInt32Marshal = NumericMarshal("=L", types.IntType)
"""unsigned, native endianity 64-bit integer"""
UNInt64Marshal = NumericMarshal("=Q", types.LongType)
"""signed, native endianity 8-bit integer"""
SNInt8Marshal = NumericMarshal("=b", types.IntType)
"""signed, native endianity 16-bit integer"""
SNInt16Marshal = NumericMarshal("=h", types.IntType)
"""signed, native endianity 32-bit integer"""
SNInt32Marshal = NumericMarshal("=l", types.IntType)
"""signed, native endianity 64-bit integer"""
SNInt64Marshal = NumericMarshal("=q", types.LongType)
"""big endian, 32-bit IEEE floating point number"""
BFloat32Marshal = NumericMarshal(">f", types.FloatType)
"""little endian, 32-bit IEEE floating point number"""
LFloat32Marshal = NumericMarshal("<f", types.FloatType)
"""native endianity, 32-bit IEEE floating point number"""
NFloat32Marshal = NumericMarshal("=f", types.FloatType)
"""big endian, 64-bit IEEE floating point number"""
BFloat64Marshal = NumericMarshal(">d", types.FloatType)
"""little endian, 64-bit IEEE floating point number"""
LFloat64Marshal = NumericMarshal("<d", types.FloatType)
"""native endianity, 64-bit IEEE floating point number"""
NFloat64Marshal = NumericMarshal("=d", types.FloatType)
