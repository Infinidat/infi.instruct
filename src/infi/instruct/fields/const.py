from . import FieldAdapter
from ..errors import InstructError
from ..serializer import FixedSizeSerializerMixin

class ConstFieldAdapter(FixedSizeSerializerMixin, FieldAdapter):
    def __init__(self, name, value, serializer=None):
        super(ConstFieldAdapter, self).__init__(name, None, serializer)
        self.value = value
        self.size = self.serializer.sizeof(value)

    def prepare_class(self, cls):
        setattr(cls, self.name, self)

    def prepare_instance(self, obj, args, kwargs):
        pass

    def write_to_stream(self, instance, stream):
        self.serializer.write_to_stream(self.value, stream)

    def read_into_from_stream(self, obj, stream):
        value = self.serializer.create_from_stream(stream)
        # TODO: assert that this is the same value

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if value != self.value:
            raise InstructError("trying to set a new value (%s) to const field %s of class %s" %
                                (value, self.name, type(instance)))

    def instance_repr(self, instance):
        return "%s (const)" % self.serializer.instance_repr(self.value)

    def validate(self, obj):
        pass
