import types
from infi.exceptools import chain

from ..serializer import StaticSerializer
from ..errors import InstructError, StructNotWellDefinedError

class FieldBase(object):
    def write_to_stream(self, instance, stream):
        raise NotImplementedError()

    def read_from_stream(self, instance, stream):
        raise NotImplementedError()

    def instance_repr(self, instance):
        raise NotImplementedError()

    def sizeof(self):
        return None

    def min_sizeof(self):
        return self.sizeof() or 0

class FieldContainer(FieldBase):
    def prepare_class(self, cls):
        raise NotImplementedError()

    def consume_field_args(self, args, kwargs):
        values = []
        for field in self.fields:
            if isinstance(field, Field):
                if field.name in kwargs:
                    values.append((field, kwargs.pop(field.name)))
                elif len(args) > 0:
                    values.append((field, args.pop(field.name)))
            elif hasattr(field, 'consume_field_args'):
                values += field.consume_field_args(args, kwargs)
        return values

    def set_instance_field_args(self, instance, values):
        for field, value in values:
            field.__set__(instance, value)

    def min_sizeof(self):
        size = 0
        for field in self.fields:
            size += field.min_sizeof()
        return size

class NamedField(FieldBase):
    def __init__(self, name):
        super(NamedField, self).__init__()
        self.name = name

class Field(NamedField):
    def __init__(self, name, serializer, default=None):
        super(Field, self).__init__(name)
        self.serializer = serializer
        if hasattr(default, 'copy'):
            self.default = default.copy()
        else:
            self.default = default

    def write_to_stream(self, instance, stream):
        self.serializer.write_instance_to_stream(self.__get__(instance, self.name), stream)

    def read_from_stream(self, instance, stream):
        self.__set__(instance, self.serializer.create_instance_from_stream(stream))
    
    def __set__(self, instance, value):
        instance._values_[self.name] = value
    
    def __get__(self, instance, owner):
        return instance._values_.get(self.name, self.default)

    def instance_repr(self, instance):
        has_value = self.name in instance._values_
        value_str = None
        if not has_value and self.default is not None:
            value_str = "%s (default)" % self.serializer.instance_repr(self.default)
        elif not has_value:
            value_str = "<not set>"
        else:
            value_str = self.serializer.instance_repr(instance._values_[self.name])
        return value_str

    def sizeof(self):
        return self.serializer.sizeof()

class ConstField(NamedField):
    def __init__(self, name, value, serializer=None):
        super(ConstField, self).__init__(name)
        self.value = value
        self.serializer = serializer or value

    def write_to_stream(self, instance, stream):
        self.serializer.write_instance_to_stream(self.value, stream)

    def read_from_stream(self, instance, stream):
        stream.read(self.serializer.sizeof())
    
    def __get__(self, instance, owner):
        return self.value

    def instance_repr(self, instance):
        return "%s (const)" % self.serializer.instance_repr(self.value)

    def sizeof(self):
        return self.serializer.sizeof()

class Padding(FieldBase):
    def __init__(self, size, char="\x00"):
        super(Padding, self).__init__()
        self.size = size
        self.char = char

    def write_to_stream(self, instance, stream):
        stream.write(self.char * self.size)

    def read_from_stream(self, instance, stream):
        stream.read(self.size)

    def sizeof(self):
        return self.size

    def instance_repr(self, instance):
        return "<%d bytes padding>" % (self.size,)

    def prepare_class(self, cls):
        pass

class PlainFieldContainer(FieldContainer):
    def __init__(self, fields):
        super(PlainFieldContainer, self).__init__()
        self.fields = fields

    def prepare_class(self, cls):
        for field in self.fields:
            if isinstance(field, NamedField):
                setattr(cls, field.name, field)
            else:
                field.prepare_class(cls)

    def write_to_stream(self, instance, stream):
        for field in self.fields:
            try:
                field.write_to_stream(instance, stream)
            except:
                raise chain(InstructError("write_to_stream failed while writing field %s" % (field,)))

    def read_from_stream(self, instance, stream):
        for field in self.fields:
            field.read_from_stream(instance, stream)

    def instance_repr(self, instance):
        buf = []
        for field in self.fields:
            if isinstance(field, NamedField):
                buf.append("%s=%s" % (field.name, field.instance_repr(instance)))
            else:
                buf.append(field.instance_repr(instance))
        return ", ".join(buf)

    def sizeof(self):
        size = 0
        for field in self.fields:
            field_size = field.sizeof()
            if field_size is None:
                return None
            size += field_size
        return size

class Struct(StaticSerializer):
    def __init__(self, *args, **kwargs):
        args = list(args)
        kwargs = kwargs.copy()
        
        cls = type(self)
        cls._init_class_fields_if_needed()
        values = cls._fields_.consume_field_args(args, kwargs)
        
        super(Struct, self).__init__(*args, **kwargs)
        self._values_ = {}

        cls._fields_.set_instance_field_args(self, values)

    @classmethod
    def create(cls, *args, **kwargs):
        cls._init_class_fields_if_needed()
            
        args = list(args)
        kwargs = kwargs.copy()
        values = cls._fields_.consume_field_args(args, kwargs)

        obj = cls(*args, **kwargs)
        cls._fields_.set_instance_field_args(obj, values)
        
        return obj

    def validate(self):
        cls = type(self)
        cls._fields_.validate(self)

    def __str__(self):
        cls = type(self)
        return("%s(%s)" % (cls.__name__, self._fields_.instance_repr(self)))

    # Serializer methods:
    
    @classmethod
    def write_instance_to_stream(cls, obj, stream):
        if obj is None:
            # TODO: exceptions
            raise ValueError("write_instance_to_stream called with a None object for class %s" % cls)

        cls._fields_.write_to_stream(obj, stream)
    
    @classmethod
    def create_instance_from_stream(cls, stream, *args, **kwargs):
        cls._init_class_fields_if_needed()
        
        args = list(args)
        kwargs = kwargs.copy()
        values = cls._fields_.consume_field_args(args, kwargs)

        obj = cls(*args, **kwargs)
        
        cls._fields_.set_instance_field_args(obj, values)

        cls._fields_.read_from_stream(obj, stream)

        return obj

    @classmethod
    def instance_repr(cls, obj):
        return str(obj)

    @classmethod
    def sizeof(cls):
        cls._init_class_fields_if_needed()
        return cls._fields_.sizeof()

    @classmethod
    def min_sizeof(cls):
        cls._init_class_fields_if_needed()
        return cls._fields_.min_sizeof()

    # Private methods:
    @classmethod
    def _init_class_fields_if_needed(cls):
        if hasattr(cls, '_struct_initialized_'):
            return
        
        if not hasattr(cls, '_fields_'):
            raise StructNotWellDefinedError("Class %s is missing a _fields_ declaration" % (cls.__name__,))
        
        fields = cls._fields_
        
        if isinstance(fields, (types.ListType, types.TupleType)):
            fields = PlainFieldContainer(fields)
        cls._fields_ = fields
        cls._fields_.prepare_class(cls)
        setattr(cls, '_struct_initialized_', True)
