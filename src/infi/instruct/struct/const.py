from . import FieldAdapter
from ..base import EMPTY_CONTEXT
from ..errors import InstructError

class ConstFieldAdapter(FieldAdapter):
    def __init__(self, name, value, io=None):
        super(ConstFieldAdapter, self).__init__(name, None, io)
        self.value = value

    def prepare_class(self, cls):
        setattr(cls, self.name, self)

    def prepare_instance(self, obj, args, kwargs):
        # Don't set the field from a kwarg.
        pass

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        self.io.write_to_stream(self.value, stream, context)

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        value = self.io.create_from_stream(stream, context, *args, **kwargs)
        if value != self.value:
            raise InstructError("constant field %s of class %s should have the value %s but instead got %s" %
                                (self.name, type(obj), self.io.to_repr(self.value), self.io.to_repr(value)))

    def __get__(self, obj, owner):
        return self.value

    def __set__(self, obj, value):
        if value != self.value:
            raise InstructError("trying to set a new value (%s) to const field %s of class %s" %
                                (value, self.name, type(obj)))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "%s (const)" % super(ConstFieldAdapter, self).to_repr(obj, context)
