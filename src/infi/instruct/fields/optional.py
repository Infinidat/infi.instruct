from . import FieldAdapter

class OptionalFieldAdapter(FieldAdapter):
    def __init__(self, name, default, serializer, predicate):
        super(OptionalFieldAdapter, self).__init__(name, default, serializer)
        self.predicate = predicate

    def write_to_stream(self, obj, stream):
        value = getattr(obj, self.name, self.default)
        if value is not None:
            self.serializer.write_to_stream(value, stream)

    def read_into_from_stream(self, obj, stream):
        if self.predicate(obj, stream):
            value = self.serializer.create_from_stream(stream)
            setattr(obj, self.name, value)

    def is_fixed_size(self):
        return False

    def min_sizeof(self):
        return 0

    def sizeof(self, obj):
        value = getattr(obj, self.name, self.default)
        if value is None:
            return 0
        return self.serializer.sizeof(value)
        
