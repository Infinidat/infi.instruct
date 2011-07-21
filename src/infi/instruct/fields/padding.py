from ..serializer import FixedSizeSerializerMixin, ModifierSerializer

class BytePaddingSerializer(FixedSizeSerializerMixin, ModifierSerializer):
    def __init__(self, size, char="\x00"):
        super(BytePaddingSerializer, self).__init__()
        self.size = size
        self.char = char

    def write_to_stream(self, obj, stream):
        stream.write(self.char * self.size)

    def read_into_from_stream(self, obj, stream):
        stream.read(self.size)

    def to_repr(self, obj):
        return "<%d bytes padding>" % (self.size,)

    def validate(self, obj):
        pass
