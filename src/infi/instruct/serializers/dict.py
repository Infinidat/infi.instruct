from ..serializer import FixedSizeSerializerMixin, CreatorSerializer

class DictSerializer(FixedSizeSerializerMixin, CreatorSerializer):
    def __init__(self, value_map, value_serializer):
        super(DictSerializer, self).__init__()
        assert value_serializer.is_fixed_size()
        self.value_map = value_map
        self.reverse_value_map = dict()
        self.value_serializer = value_serializer
        self.size = self.value_serializer.min_sizeof()
        for key, value in value_map.items():
            assert value not in self.reverse_value_map
            self.reverse_value_map[value] = key
        
    def create_from_stream(self, stream, *args, **kwargs):
        value = self.value_serializer.create_from_stream(stream, *args, **kwargs)
        return self.reverse_value_map[value]

    def write_to_stream(self, obj, stream):
        value = self.value_map[obj]
        self.value_serializer.write_to_stream(value, stream)
        
    def to_repr(self, obj):
        return obj
