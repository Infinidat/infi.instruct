from .base import FixedSizer, Marshal, EMPTY_CONTEXT

class FixedSizeMappingMarshal(FixedSizer, Marshal):
    def __init__(self, value_map, value_marshal):
        super(FixedSizeMappingMarshal, self).__init__()
        assert value_marshal.is_fixed_size()
        self.value_map = value_map
        self.value_marshal = value_marshal
        self.reverse_value_map = dict()
        self.size = self.value_marshal.min_max_sizeof().min
        for key, value in value_map.items():
            assert value not in self.reverse_value_map
            self.reverse_value_map[value] = key
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        value = self.value_marshal.create_from_stream(stream, context, *args, **kwargs)
        return self.reverse_value_map[value]

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        value = self.value_map[obj]
        self.value_marshal.write_to_stream(value, stream, context)
