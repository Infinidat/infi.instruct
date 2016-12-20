from __future__ import absolute_import

import struct
from infi.exceptools import chain as chain_exceptions

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
        except struct.error:
            raise chain_exceptions(InstructError("Unpacking error occurred"))

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        try:
            stream.write(struct.pack(self.format_string, obj))
        except struct.error:
            raise chain_exceptions(InstructError("Packing error occurred"))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        if self.type is int:
            return context.get('int_repr_format', '%d') % obj
        elif self.type == float:
            return context.get('float_repr_format', '%f') % obj
        return repr(obj)

"""unsigned, big endian 8-bit integer"""
UBInt8Marshal = NumericMarshal(">B", int)
"""unsigned, big endian 16-bit integer"""
UBInt16Marshal = NumericMarshal(">H", int)
"""unsigned, big endian 32-bit integer"""
UBInt32Marshal = NumericMarshal(">L", int)
"""unsigned, big endian 64-bit integer"""
UBInt64Marshal = NumericMarshal(">Q", int)
"""signed, big endian 8-bit integer"""
SBInt8Marshal = NumericMarshal(">b", int)
"""signed, big endian 16-bit integer"""
SBInt16Marshal = NumericMarshal(">h", int)
"""signed, big endian 32-bit integer"""
SBInt32Marshal = NumericMarshal(">l", int)
"""signed, big endian 64-bit integer"""
SBInt64Marshal = NumericMarshal(">q", int)
"""unsigned, little endian 8-bit integer"""
ULInt8Marshal = NumericMarshal("<B", int)
"""unsigned, little endian 16-bit integer"""
ULInt16Marshal = NumericMarshal("<H", int)
"""unsigned, little endian 32-bit integer"""
ULInt32Marshal = NumericMarshal("<L", int)
"""unsigned, little endian 64-bit integer"""
ULInt64Marshal = NumericMarshal("<Q", int)
"""signed, little endian 8-bit integer"""
SLInt8Marshal = NumericMarshal("<b", int)
"""signed, little endian 16-bit integer"""
SLInt16Marshal = NumericMarshal("<h", int)
"""signed, little endian 32-bit integer"""
SLInt32Marshal = NumericMarshal("<l", int)
"""signed, little endian 64-bit integer"""
SLInt64Marshal = NumericMarshal("<q", int)
"""unsigned, native endianity 8-bit integer"""
UNInt8Marshal = NumericMarshal("=B", int)
"""unsigned, native endianity 16-bit integer"""
UNInt16Marshal = NumericMarshal("=H", int)
"""unsigned, native endianity 32-bit integer"""
UNInt32Marshal = NumericMarshal("=L", int)
"""unsigned, native endianity 64-bit integer"""
UNInt64Marshal = NumericMarshal("=Q", int)
"""signed, native endianity 8-bit integer"""
SNInt8Marshal = NumericMarshal("=b", int)
"""signed, native endianity 16-bit integer"""
SNInt16Marshal = NumericMarshal("=h", int)
"""signed, native endianity 32-bit integer"""
SNInt32Marshal = NumericMarshal("=l", int)
"""signed, native endianity 64-bit integer"""
SNInt64Marshal = NumericMarshal("=q", int)
"""big endian, 32-bit IEEE floating point number"""
BFloat32Marshal = NumericMarshal(">f", float)
"""little endian, 32-bit IEEE floating point number"""
LFloat32Marshal = NumericMarshal("<f", float)
"""native endianity, 32-bit IEEE floating point number"""
NFloat32Marshal = NumericMarshal("=f", float)
"""big endian, 64-bit IEEE floating point number"""
BFloat64Marshal = NumericMarshal(">d", float)
"""little endian, 64-bit IEEE floating point number"""
LFloat64Marshal = NumericMarshal("<d", float)
"""native endianity, 64-bit IEEE floating point number"""
NFloat64Marshal = NumericMarshal("=d", float)
