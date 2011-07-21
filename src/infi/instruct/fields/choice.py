from . import FieldAdapter
from ..serializer import CreatorSerializer

class ChoiceSerializer(CreatorSerializer):
    def __init__(self, serializer_choice_func, deserializer_choice_func, min_size=0, size=None):
        self.serializer_choice_func = serializer_choice_func
        self.deserializer_choice_func = deserializer_choice_func
        self.min_size = min_size
        self.size = size
    
    def write_to_stream(self, obj, stream):
        serializer = self.serializer_choice_func(obj)
        serializer.write_to_stream(obj, stream)

    def create_from_stream(self, stream, *args, **kwargs):
        serializer = self.deserializer_choice_func(stream)
        return serializer.create_from_stream(stream, *args, **kwargs)

    def sizeof(self, obj):
        if self.size is not None:
            return self.size
        return self.serializer_choice_func(obj).sizeof(obj)

    def min_sizeof(self):
        return self.min_size

    def is_fixed_size(self):
        return self.size is not None

    def validate(self, obj):
        return self.serializer_choice_func(obj).validate(obj)

    def to_repr(self, obj):
        return self.serializer_choice_func(obj).to_repr(obj)
    
class ChoiceFieldAdapter(FieldAdapter):
    def __init__(self, name, default, choice_func, serializer_map):
        self.all_fixed_size = all(map(lambda serializer: serializer.is_fixed_size(), serializer_map.values()))
        self.size = None
        self.min_size = min(map(lambda serializer: serializer.min_sizeof(), serializer_map.values()))
        if self.all_fixed_size:
            self.size = max(map(lambda serializer: serializer.min_sizeof(), serializer_map.values()))
            if self.min_size != self.size:
                self.size = None
        serializer = ChoiceSerializer(self._get_serializer, self._get_deserializer, self.min_size, self.size)
        super(ChoiceFieldAdapter, self).__init__(name, default, serializer)
        
        self.choice_func = choice_func
        self.serializer_map = serializer_map

    def _get_serializer(self, obj):
        return self.serializer_map[self.choice_func(self.current_obj)]

    def _get_deserializer(self, stream):
        return self.serializer_map[self.choice_func(self.current_obj)]

    def write_to_stream(self, obj, stream):
        self.current_obj = obj
        try:
            super(ChoiceFieldAdapter, self).write_to_stream(obj, stream)
        finally:
            self.current_obj = None

    def read_into_from_stream(self, obj, stream):
        self.current_obj = obj
        try:
            super(ChoiceFieldAdapter, self).read_into_from_stream(obj, stream)
        finally:
            self.current_obj = None
