from numbers import Number
from .reference import Reference, NumericReference

class Field(object):
    value_getter = None
    value_setter = None
    serializer = None
    deserializer = None
    position = None
    name = None
    before_pack = None
    before_unpack = None

    def __init__(self, value_getter, value_setter, serializer, deserializer, position, name=None,
                 before_pack=None, before_unpack=None):
        """
        Arguments and their types:

        function value_getter(obj): value
        function value_setter(obj, value): void
        function serializer(obj, value): buffer
        function deserializer(obj, buffer): value
        Reference or [ slice, ..., slice ] position
        string name
        function before_pack(field, obj): void
        function before_unpack(field, obj): void
        """
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.serializer = serializer
        self.deserializer = deserializer
        self.position = position
        self.name = name
        self.before_pack = before_pack
        self.before_unpack = before_unpack

    def pack(self, obj, output_buffer):
        if self.before_pack:
            self.before_pack(self, obj)
        value = self.value_getter(obj)
        buf = self.serializer(obj, value)
        output_buffer.set(buf, Reference.dereference(self.position, obj))

    def unpack(self, obj, input_buffer):
        if self.before_unpack:
            self.before_unpack(self, obj)
        buf = input_buffer.get(Reference.dereference(self.position, obj))
        value, _ = self.deserializer(obj, buf)
        self.value_setter(obj, value)

class AttributeAccessorFactory(object):
    @classmethod
    def create_getter_with_default(self, attr_name, default_value=None):
        def getter(obj):
            return getattr(obj, attr_name, default_value)
        return getter

    @classmethod
    def create_setter_with_default(self, attr_name, default_value=None):
        def setter(obj, value):
            if value is None and default_value is not None:
                setattr(obj, attr_name, default_value)
            else:
                setattr(obj, attr_name, value)
        return setter

    @classmethod
    def create_getter(self, attr_name):
        def getter(obj):
            return getattr(obj, attr_name)
        return getter

    @classmethod
    def create_setter(self, attr_name):
        def setter(obj, value):
            setattr(obj, attr_name, value)
        return setter

class ConstAttributeAccessorFactory(object):
    @classmethod
    def create_getter(self, attr_name, const_value):
        def getter(obj):
            return const_value
        return getter

    @classmethod
    def create_setter(self, attr_name, const_value):
        def setter(obj, value):
            setattr(obj, attr_name, const_value)
        return setter

class FieldReference(Field, Reference):
    def __init__(self, value_getter, value_setter, serializer, deserializer, position, name=None,
                 before_pack=None, before_unpack=None):
        Field.__init__(self, value_getter, value_setter, serializer, deserializer, position, name, before_pack,
                       before_unpack)
        Reference.__init__(self)

    def get_children(self):
        return [ self.position, self.before_pack ]

    def needs_object_for_value(self):
        # FIXME: check before_pack and constness
        return True

    def value(self, obj):
        return self.value_getter(obj)

    def __repr__(self):
        return "ref({0})".format(self._name())

    def _name(self):
        return self.name if self.name is not None else "<unknown>"

class NumericFieldReference(FieldReference, NumericReference):
    def value(self, obj):
        value = self.value_getter(obj)
        if not isinstance(value, Number):
            raise TypeError("field {0} of class {1} should have a numeric value but instead it's {2}".format(
                self._name(), obj.__class__))
        return value

    def __repr__(self):
        return "num_ref({0})".format(self._name())
