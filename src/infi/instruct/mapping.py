from .base import FixedSizer, AllocatingReader, Writer, ReprCapable, EMPTY_CONTEXT

class MappingIO(FixedSizer, AllocatingReader, Writer, ReprCapable):
    def __init__(self, value_map, value_io):
        super(MappingIO, self).__init__()
        assert value_io.is_fixed_size()
        self.value_map = value_map
        self.value_io = value_io
        self.reverse_value_map = dict()
        self.size = self.value_io.min_max_sizeof().min
        for key, value in value_map.items():
            assert value not in self.reverse_value_map
            self.reverse_value_map[value] = key
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        value = self.value_io.create_from_stream(stream, context, *args, **kwargs)
        return self.reverse_value_map[value]

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        value = self.value_map[obj]
        self.value_io.write_to_stream(value, stream, context)
        
    def to_repr(self, obj):
        return obj
