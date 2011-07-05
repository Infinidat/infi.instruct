import struct
from ..errors import InstructError, NotEnoughDataError
from ..serializer import DynamicSerializer
from infi.exceptools import chain

class PrimitiveSerializer(DynamicSerializer):
    def __init__(self, format_string):
        self.format_string = format_string
        self.size = struct.calcsize(format_string)

    def create_instance_from_stream(self, stream):
        packed_value = stream.read(self.size)
        if len(packed_value) < self.size:
            # TODO: exception better reporting
            raise NotEnoughDataError("expected to read %d bytes but read only %d bytes instead" %
                                     (self.size, len(packed_value)))
        try:
            return struct.unpack(self.format_string, packed_value)[0]
        except struct.error, e:
            # TODO: exception better reporting
            raise chain(InstructError("Unpacking error occurred"))

    def write_instance_to_stream(self, instance, stream):
        if instance is None:
            raise InstructError("Cannot serialize None as a primitive value %s" % cls)
    
        try:
            stream.write(struct.pack(self.format_string, instance))
        except struct.error, e:
            raise chain(InstructError("Packing error occurred"))

    def sizeof(self):
        return self.size

    def instance_repr(self, instance):
        return repr(instance)

"""unsigned, big endian 8-bit integer"""
UBInt8Serializer = PrimitiveSerializer(">B")
"""unsigned, big endian 16-bit integer"""
UBInt16Serializer = PrimitiveSerializer(">H")
"""unsigned, big endian 32-bit integer"""
UBInt32Serializer = PrimitiveSerializer(">L")
"""unsigned, big endian 64-bit integer"""
UBInt64Serializer = PrimitiveSerializer(">Q")
"""signed, big endian 8-bit integer"""
SBInt8Serializer = PrimitiveSerializer(">b")
"""signed, big endian 16-bit integer"""
SBInt16Serializer = PrimitiveSerializer(">h")
"""signed, big endian 32-bit integer"""
SBInt32Serializer = PrimitiveSerializer(">l")
"""signed, big endian 64-bit integer"""
SBInt64Serializer = PrimitiveSerializer(">q")
"""unsigned, little endian 8-bit integer"""
ULInt8Serializer = PrimitiveSerializer("<B")
"""unsigned, little endian 16-bit integer"""
ULInt16Serializer = PrimitiveSerializer("<H")
"""unsigned, little endian 32-bit integer"""
ULInt32Serializer = PrimitiveSerializer("<L")
"""unsigned, little endian 64-bit integer"""
ULInt64Serializer = PrimitiveSerializer("<Q")
"""signed, little endian 8-bit integer"""
SLInt8Serializer = PrimitiveSerializer("<b")
"""signed, little endian 16-bit integer"""
SLInt16Serializer = PrimitiveSerializer("<h")
"""signed, little endian 32-bit integer"""
SLInt32Serializer = PrimitiveSerializer("<l")
"""signed, little endian 64-bit integer"""
SLInt64Serializer = PrimitiveSerializer("<q")
"""unsigned, native endianity 8-bit integer"""
UNInt8Serializer = PrimitiveSerializer("=B")
"""unsigned, native endianity 16-bit integer"""
UNInt16Serializer = PrimitiveSerializer("=H")
"""unsigned, native endianity 32-bit integer"""
UNInt32Serializer = PrimitiveSerializer("=L")
"""unsigned, native endianity 64-bit integer"""
UNInt64Serializer = PrimitiveSerializer("=Q")
"""signed, native endianity 8-bit integer"""
SNInt8Serializer = PrimitiveSerializer("=b")
"""signed, native endianity 16-bit integer"""
SNInt16Serializer = PrimitiveSerializer("=h")
"""signed, native endianity 32-bit integer"""
SNInt32Serializer = PrimitiveSerializer("=l")
"""signed, native endianity 64-bit integer"""
SNInt64Serializer = PrimitiveSerializer("=q")
"""big endian, 32-bit IEEE floating point number"""
BFloat32Serializer = PrimitiveSerializer(">f")
"""little endian, 32-bit IEEE floating point number"""
LFloat32Serializer = PrimitiveSerializer("<f")
"""native endianity, 32-bit IEEE floating point number"""
NFloat32Serializer = PrimitiveSerializer("=f")
"""big endian, 64-bit IEEE floating point number"""
BFloat64Serializer = PrimitiveSerializer(">d")
"""little endian, 64-bit IEEE floating point number"""
LFloat64Serializer = PrimitiveSerializer("<d")
"""native endianity, 64-bit IEEE floating point number"""
NFloat64Serializer = PrimitiveSerializer("=d")
