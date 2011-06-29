from . import PlainFieldContainer, FieldBase, Field
from ..serializer import DynamicSerializer
from ..errors import BitFieldNotInByteBoundry, FieldTypeNotSupportedError

class BitStringIO(object):
    def __init__(self, byte_size_or_array):
        self.position = 0
        self.value = bytearray(byte_size_or_array)

    def getvalue(self):
        return str(self.value)

    def write(self, value, bits_to_write):
        if (bits_to_write + self.position) > len(self.value) * 8:
            raise IOError("attempting to write past the end of the buffer")

        byte_i, bit_i = (self.position / 8, self.position % 8)

        bits_written = 0
        if bit_i != 0:
            chunk_to_write = min(8 - bit_i, bits_to_write)
            bitmask = (1 << chunk_to_write) - 1
            self.value[byte_i] |= (value & bitmask) << bit_i
            byte_i += 1
            bits_written = chunk_to_write

        for n in xrange(bits_written, bits_to_write, 8):
            chunk_to_write = min(8, bits_to_write - n)
            bitmask = (1 << chunk_to_write) - 1
            self.value[byte_i] |= (value >> n) & bitmask
            byte_i += 1
        
        self.position += bits_to_write

    def read(self, bits_to_read):
        if len(self.value) * 8 < (bits_to_read + self.position):
            raise IOError("attempting to read past the end of the buffer")
        
        byte_i, bit_i = (self.position / 8, self.position % 8)
        result = 0
        bits_read = 0

        if bit_i != 0:
            chunk_to_read = min(8 - bit_i, bits_to_read)
            bitmask = (1 << chunk_to_read) - 1
            result = (self.value[byte_i] >> bit_i) & bitmask
            bits_read = chunk_to_read
            byte_i += 1

        for n in xrange(bits_read, bits_to_read, 8):
            chunk_to_read = min(8, bits_to_read - n)
            bitmask = (1 << chunk_to_read) - 1
            result |= (self.value[byte_i] & bitmask) << n
            byte_i += 1

        self.position += bits_to_read
        return result

class BitSerializer(DynamicSerializer):
    def __init__(self, bit_size):
        self.bit_size = bit_size

    def create_instance_from_stream(self, stream, *args, **kwargs):
        return stream.read(self.bit_size)

    def write_instance_to_stream(self, instance, stream):
        stream.write(instance, self.bit_size)

    def instance_repr(self, instance):
        return str(instance)

class BitField(Field):
    def __init__(self, name, bit_size, default=None):
        super(BitField, self).__init__(name, BitSerializer(bit_size), default)
        self.bit_size = bit_size

    def bit_sizeof(self):
        return self.bit_size

class BitPadding(FieldBase):
    def __init__(self, bit_size):
        super(BitPadding, self).__init__()
        self.bit_size = bit_size

    def write_to_stream(self, instance, stream):
        stream.write(0, self.bit_size)

    def read_from_stream(self, instance, stream):
        stream.read(self.bit_size)

    def sizeof(self):
        return None

    def bit_sizeof(self):
        return self.bit_size

    def instance_repr(self, instance):
        return "<%d bits padding>" % (self.bit_size,)

    def prepare_class(self, cls):
        pass

class BitFieldContainer(PlainFieldContainer):
    def __init__(self, fields):
        super(BitFieldContainer, self).__init__(fields)
        self.bit_size = 0
        self.size = 0
        
        for field in fields:
            if not hasattr(field, 'bit_sizeof'):
                raise FieldTypeNotSupportedError("Field %s not supported inside a bit field container" % str(field))
            self.bit_size += field.bit_sizeof()
            
        if (self.bit_size % 8) != 0:
            raise BitFieldNotInByteBoundry("Bit field container must have a byte boundry")

        self.size = self.bit_size / 8

    def write_to_stream(self, instance, stream):
        bit_stream = BitStringIO(self.size)
        for field in self.fields:
            field.write_to_stream(instance, bit_stream)
        stream.write(bit_stream.getvalue())

    def read_from_stream(self, instance, stream):
        bit_stream = BitStringIO(stream.read(self.size))
        for field in self.fields:
            field.read_from_stream(instance, bit_stream)
        
    def sizeof(self):
        return self.size
