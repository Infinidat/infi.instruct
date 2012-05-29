import struct

class UBInt32Serialize(object):
    @classmethod
    def serialize(cls, obj, value):
        return struct.pack(">L", value)

    @classmethod
    def deserialize(cls, obj, buffer):
        return (struct.unpack(">L", str(buffer[0:4]))[0], 4)

class StringSerialize(object):
    @classmethod
    def serialize(cls, obj, value):
        return value

    @classmethod
    def deserialize(cls, obj, buffer):
        return (buffer, len(buffer))

class BufferSerialize(object):
    @classmethod
    def serialize(cls, obj, value):
        return value.pack()

    @classmethod
    def create_deserialize(cls, type):
        def deserialize(obj, buffer):
            value = type()
            size = value.unpack(buffer)
            return (value, size)

class ArraySerialize(object):
    @classmethod
    def create_serialize(cls, type_serialize):
        def serialize(obj, value):
            result = bytearray()
            for elem in value:
                result += type_serialize(obj, elem)
            return result
        return serialize

    @classmethod
    def create_deserialize(cls, type_deserialize):
        def deserialize(obj, buffer):
            result = []
            buffer_ofs = 0
            while buffer_ofs < len(buffer):
                value, size = type_deserialize(obj, buffer[buffer_ofs:])
                result.append(value)
                buffer_ofs += size
            return result, buffer_ofs
        return deserialize
