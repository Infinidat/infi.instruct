from ..utils.read_ahead_stream import ReadAheadStream
from ..errors import InstructError
from ..serializer import CreatorSerializer

class ReadAheadSelectorSerializer(CreatorSerializer):
    def __init__(self, serializer_factory_func, deserializer_factory_func, min_size=0, fixed_size=False):
        self.serializer_factory_func = serializer_factory_func
        self.deserializer_factory_func = deserializer_factory_func
        self.min_size = min_size
        self.all_fixed_size = fixed_size

    def create_from_stream(self, stream, *args, **kwargs):
        rstream = ReadAheadStream(stream)
        rstream.set_read_ahead(True)
        deserializer = self.deserializer_factory_func(rstream)
        rstream.set_read_ahead(False)
        result = deserializer.create_from_stream(rstream, *args, **kwargs)
        assert rstream.is_read_ahead_empty()
        return result

    def write_to_stream(self, obj, stream):
        serializer = self.serializer_factory_func(obj)
        serializer.write_to_stream(obj, stream)
    
    def min_sizeof(self):
        return self.min_size
    
    def sizeof(self, obj):
        serializer = self.serializer_factory_func(obj)
        return serializer.sizeof(obj)
    
    def is_fixed_size(self):
        return self.all_fixed_size
    
    def validate(self, obj):
        serializer = self.serializer_factory_func(obj)
        serializer.validate(obj)
    
    def to_repr(self, obj):
        serializer = self.serializer_factory_func(obj)
        return serializer.to_repr(obj)
