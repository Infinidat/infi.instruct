from ..errors import InstructError
from ..serializers.select import ReadAheadSelectorSerializer

class StructSelectorSerializer(ReadAheadSelectorSerializer):
    def __init__(self, selector_deserializer, select_map, default=None):
        serializers = select_map.values()
        if default is not None:
            serializers.append(default)
        min_size = min([ s.min_sizeof() for s in serializers ])
        all_fixed_size = all([ s.is_fixed_size() for s in serializers ])
        if all_fixed_size:
            all_fixed_size = min_size == max([ s.min_sizeof() for s in serializers ])
        
        super(StructSelectorSerializer, self).__init__(self._serializer_factory, self._deserializer_factory,
                                                       min_size, all_fixed_size)
                                                       
        self.selector_deserializer = selector_deserializer
        self.select_map = select_map
        self.default = default

    def _serializer_factory(self, obj):
        return obj._serializer_

    def _deserializer_factory(self, stream):
        index = self.selector_deserializer.create_from_stream(stream)
        if index in self.select_map:
            return self.select_map[index]
        if self.default is not None:
            return self.default
        raise InstructError("no mapping was found for value %s" % (self.selector_deserializer.to_repr(index),))
