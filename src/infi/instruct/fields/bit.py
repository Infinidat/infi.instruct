from ..serializer import CreatorSerializer, FixedSizeSerializerMixin, ModifierSerializer
from ..errors import BitFieldNotInByteBoundry, FieldTypeNotSupportedError
from . import FieldListSerializer
from .bitstringio import BitStringIO

class BitSerializer(FixedSizeSerializerMixin, CreatorSerializer):
    def __init__(self, bit_size):
        super(BitSerializer, self).__init__()
        self.size = bit_size

    def create_from_stream(self, stream, *args, **kwargs):
        return stream.read(self.size)

    def write_to_stream(self, obj, stream):
        stream.write(obj, self.size)

    def to_repr(self, obj):
        return str(obj)

    def validate(self, obj):
        # TODO: validate
        pass

class BitPaddingSerializer(FixedSizeSerializerMixin, ModifierSerializer):
    def __init__(self, size):
        super(BitPaddingSerializer, self).__init__()
        self.size = size

    def read_into_from_stream(self, obj, stream):
        stream.read(self.size)

    def write_to_stream(self, obj, stream):
        stream.write(0, self.size)

    def to_repr(self, obj):
        return "<%d bits padding>" % (self.size,)

    def validate(self, obj):
        pass

class BitFieldListSerializer(FixedSizeSerializerMixin, FieldListSerializer):
    def __init__(self, serializers):
        super(BitFieldListSerializer, self).__init__(serializers)
        self.bit_size = 0
        self.size = 0
        
        for serializer in self.serializers:
            # TODO: make sure we're dealing with bit fields here.
            self.bit_size += serializer.min_sizeof()
            
        if (self.bit_size % 8) != 0:
            raise BitFieldNotInByteBoundry("Bit field container must have a byte boundry")

        self.size = self.bit_size / 8

    def write_to_stream(self, obj, stream):
        bit_stream = BitStringIO(self.size)
        for serializer in self.serializers:
            serializer.write_to_stream(obj, bit_stream)
        stream.write(bit_stream.getvalue())

    def read_into_from_stream(self, obj, stream):
        bit_stream = BitStringIO(stream.read(self.size))
        for serializer in self.serializers:
            serializer.read_into_from_stream(obj, bit_stream)
