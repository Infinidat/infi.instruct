from ..base import MinMax, EMPTY_CONTEXT
from . import Field

class OptionalField(Field):
    def __init__(self, name, marshal, predicate, default=None):
        super(OptionalField, self).__init__(name, marshal, default)
        self.predicate = predicate

    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        value = self.get_value(obj)
        if value is not None:
            self.marshal.write_to_stream(value, stream, context)

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        if self.predicate(obj, stream, context):
            super(OptionalField, self).read_fields(obj, stream, context, *args, **kwargs)

    def sizeof(self, obj):
        value = self.get_value(obj)
        if value is None:
            return 0
        return self.marshal.sizeof(value)
        
    def min_max_sizeof(self):
        return MinMax(0, self.marshal.min_max_sizeof().max)
