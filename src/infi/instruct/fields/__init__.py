import types
import functools
from infi.exceptools import chain

from ..serializer import ModifierSerializer, AggregateModifierSerializer
from ..errors import InstructError, StructNotWellDefinedError

def copy_if_supported(obj):
    return obj.copy() if hasattr(obj, 'copy') else obj

class FieldAdapter(ModifierSerializer):
    def __init__(self, name, default, serializer):
        super(FieldAdapter, self).__init__()
        self.name = name
        self.default = default
        self.serializer = serializer

    def min_sizeof(self):
        return self.serializer.min_sizeof()

    def sizeof(self, obj):
        value = getattr(obj, self.name, self.default)
        return self.serializer.sizeof(value)

    def is_fixed_size(self):
        return self.serializer.is_fixed_size()

    def validate(self, obj):
        value = getattr(obj, self.name, None)
        self.serializer.validate(value)

    def to_repr(self, obj):
        value = getattr(obj, self.name, None)
        return "%s=%s" % (self.name, self.serializer.to_repr(value) if value is not None else "<not set>")
    
    def read_into_from_stream(self, obj, stream):
        try:
            value = self.serializer.create_from_stream(stream)
        except InstructError, e:
            raise chain(InstructError("Error occurred while reading field '%s' for class %s" % (self.name, type(obj))))
                
        setattr(obj, self.name, value)

    def write_to_stream(self, obj, stream):
        value = getattr(obj, self.name, None)
        try:
            self.serializer.write_to_stream(value, stream)
        except InstructError, e:
            raise chain(InstructError("Error occurred while writing field '%s' for class %s" % (self.name, type(obj))))

    def prepare_instance(self, obj, args, kwargs):
        if self.name in kwargs:
            setattr(obj, self.name, kwargs.pop(self.name))
        else:
            setattr(obj, self.name, copy_if_supported(self.default))

class FieldListSerializer(AggregateModifierSerializer):
    def __init__(self, serializers):
        super(FieldListSerializer, self).__init__(serializers)

    def prepare_class(self, cls):
        for serializer in self.serializers:
            if hasattr(serializer, 'prepare_class'):
                serializer.prepare_class(cls)

    def prepare_instance(self, obj, args, kwargs):
        # Called from the modified __init__ method of the class.
        # We made this a separate method so all the defaults will be initialized before the user's ctor is called.
        for serializer in self.serializers:
            if hasattr(serializer, 'prepare_instance'):
                serializer.prepare_instance(obj, args, kwargs)

    def to_repr(self, obj):
        return "(" + super(FieldListSerializer, self).to_repr(obj) + ")"

class StructType(type):
    def __new__(cls, name, bases, attrs):
        # If we initialize our own class don't do any modifications.
        if name == "Struct":
            return super(StructType, cls).__new__(cls, name, bases, attrs)

        if "_fields_" not in attrs:
            raise StructNotWellDefinedError("Class %s is missing a _fields_ declaration" % (name,))

        fields = attrs["_fields_"]
        if isinstance(fields, (types.ListType, types.TupleType)):
            fields = FieldListSerializer(fields)

        attrs["_serializer_"] = fields

        # We want to first put our own __init__ method that will initialize all the fields passed by kwargs and then
        # call the user's __init__ method (if exists) with args/kwargs left.
        if "__init__" in attrs:
            prev_init = attrs["__init__"]
            del attrs["__init__"]
        else:
            prev_init = None
        
        new_cls = super(StructType, cls).__new__(cls, name, bases, attrs)
        fields.prepare_class(new_cls)
        setattr(new_cls, "__init__", cls._create_struct_class_init(new_cls, prev_init))
        return new_cls

    @classmethod
    def _create_struct_class_init(cls, new_cls, prev_init):
        def __instance_init__(self, *args, **kwargs):
            new_cls._serializer_.prepare_instance(self, args, kwargs)
            if prev_init is None:
                super(new_cls, self).__init__(*args, **kwargs)
            else:
                prev_init(self, *args, **kwargs)
        return __instance_init__

class Struct(object):
    __metaclass__ = StructType

    @classmethod
    def write_to_stream(cls, obj, stream):
        type(obj)._serializer_.write_to_stream(obj, stream)

    @classmethod
    def create_from_string(cls, string, *args, **kwargs):
        obj = cls(*args, **kwargs)
        cls._serializer_.read_into_from_string(obj, string)
        return obj

    @classmethod
    def create_from_stream(cls, stream, *args, **kwargs):
        obj = cls(*args, **kwargs)
        cls._serializer_.read_into_from_stream(obj, stream)
        return obj

    @classmethod
    def min_sizeof(cls):
        return cls._serializer_.min_sizeof()
    
    @classmethod
    def sizeof(cls, instance):
        return cls._serializer_.sizeof(instance)

    @classmethod
    def is_fixed_size(cls):
        return cls._serializer_.is_fixed_size()

    @classmethod
    def validate(self, obj):
        type(obj)._serializer_.validate(instance)

    @classmethod
    def to_string(cls, obj):
        return type(obj)._serializer_.to_string(obj)

    @classmethod
    def to_repr(cls, obj):
        return repr(obj)

    def write_to_stream(self, stream):
        type(self)._serializer_.write_to_stream(self, stream)
        
    def read_into_from_string(self, string):
        type(self)._serializer_.read_into_from_string(self, string)

    def read_into_from_stream(self, stream):
        type(self)._serializer_.read_into_from_stream(self, stream)

    def sizeof(self):
        return type(self)._serializer_.sizeof(self)

    def __str__(self):
        return type(self)._serializer_.to_string(self)

    def __repr__(self):
        cls = type(self)
        return("%s%s" % (cls.__name__, self._serializer_.to_repr(self)))

    # Backward compatibility (0.10)
    # BEGIN DEPRECATION
    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    create_instance_from_stream = create_from_stream
    create_instance_from_string = create_from_string
    write_instance_to_stream = write_to_stream
    instance_to_string = to_string
    # END DEPRECATION
