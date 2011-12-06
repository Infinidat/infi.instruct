from . import Field
from ..base import EMPTY_CONTEXT
from ..errors import InstructError

class ConstField(Field):
    def __init__(self, name, marshal, value):
        super(ConstField, self).__init__(name, marshal)
        self.value = value

    def prepare_class(self, cls):
        setattr(cls, self.name, self)

    def prepare_instance(self, obj, args, kwargs):
        # Don't set the field from a kwarg.
        # TODO: take the key from the kwargs if exists and compare it to value?
        pass

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        value = self.marshal.create_from_stream(stream, context, *args, **kwargs)
        if value != self.value:
            raise InstructError("constant field %s of class %s should have the value %s but instead got %s" %
                                (self.name, type(obj), self.marshal.to_repr(self.value, context),
                                 self.marshal.to_repr(value, context)))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "%s (const)" % super(ConstField, self).to_repr(obj, context)

    def get_value(self, obj):
        return self.value

    def set_value(self, obj, value):
        pass

    def __get__(self, obj, owner):
        return self.value

    def __set__(self, obj, value):
        if value != self.value:
            raise InstructError("trying to set a new value (%s) to const field %s of class %s" %
                                (value, self.name, type(obj)))

