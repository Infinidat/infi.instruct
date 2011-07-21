from ..serializer import CreatorSerializer, FixedSizeSerializerMixin
from ..errors import InvalidValueError

class FixedSizeStringSerializer(FixedSizeSerializerMixin, CreatorSerializer):
    def __init__(self, size, padding='\x00'):
        super(FixedSizeStringSerializer, self).__init__()
        self.size = size
        self.padding = padding
        assert len(self.padding) == 1
        
    def create_from_stream(self, stream, *args, **kwargs):
        obj = stream.read(self.size)
        return obj.rstrip(self.padding)

    def write_to_stream(self, obj, stream):
        if len(obj) > self.size:
            raise InvalidValueError("fixed-size string length is expected to be of length %d or smaller but instead got %d (string=%s)" % (self.size, len(obj), repr(obj)))
        stream.write(obj)
        if len(obj) < self.size:
            stream.write(self.padding * (self.size - len(obj)))

    def to_repr(self, obj):
        return repr(obj)

class FixedSizeBufferSerializer(FixedSizeSerializerMixin, CreatorSerializer):
    def __init__(self, size):
        super(FixedSizeBufferSerializer, self).__init__()
        self.size = size
        
    def create_from_stream(self, stream, *args, **kwargs):
        return stream.read(self.size)

    def write_to_stream(self, obj, stream):
        if len(obj) != self.size:
            raise InvalidValueError("fixed-size buffer length is expected to be of length %d but instead got %d (buffer=%s)" % (self.size, len(obj), repr(obj)))
        stream.write(obj)

    def to_repr(self, obj):
        return repr(obj)

class VarSizeBufferSerializer(CreatorSerializer):
    def __init__(self, size_serializer):
        super(VarSizeBufferSerializer, self).__init__()
        self.size_serializer = size_serializer
        assert self.size_serializer.is_fixed_size()
    
    def create_from_stream(self, stream, *args, **kwargs):
        size = self.size_serializer.create_from_stream(stream)
        return stream.read(size)
    
    def write_to_stream(self, obj, stream):
        self.size_serializer.write_to_stream(len(obj))
        stream.write(obj)

    def is_fixed_size(self):
        return False

    def min_sizeof(self):
        return self.size_serializer.min_sizeof()

    def sizeof(self, obj):
        return self.size_serializer.min_sizeof() + len(obj)

    def validate(self, obj):
        pass
    
    def to_repr(self, obj):
        return repr(obj)
