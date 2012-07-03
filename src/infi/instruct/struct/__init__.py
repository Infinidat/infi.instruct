import types
from cStringIO import StringIO

from ..base import MarshalBase, WritableContext, EMPTY_CONTEXT, ZERO_MIN_MAX
from ..errors import StructNotWellDefinedError

def copy_if_supported(obj):
    return obj.copy() if hasattr(obj, 'copy') else obj

class FieldMarshal(MarshalBase):
    def prepare_class(self, cls):
        pass
    
    def prepare_instance(self, obj, args, kwargs):
        pass
    
    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        raise NotImplementedError()
    
    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        raise NotImplementedError()

class FieldBase(FieldMarshal):
    def __init__(self, marshal):
        super(FieldBase, self).__init__()
        self.marshal = marshal

    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        self.marshal.write_to_stream(self.get_value(obj), stream, context)

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        self.set_value(obj, self.marshal.create_from_stream(stream, context, *args, **kwargs))
        
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return self.marshal.to_repr(self.get_value(obj), context)

    def sizeof(self, obj):
        return self.marshal.sizeof(self.get_value(obj))

    def min_max_sizeof(self):
        return self.marshal.min_max_sizeof()

    def set_value(self, obj, value):
        pass

    def get_value(self, obj):
        return None

class AnonymousField(FieldBase):
    def __init__(self, marshal):
        super(AnonymousField, self).__init__(marshal)

    def __str__(self):
        return "anonymous field"

class Field(FieldBase):
    def __init__(self, name, marshal, default=None):
        super(Field, self).__init__(marshal)
        self.name = name
        self.default = default
    
    def prepare_instance(self, obj, args, kwargs):
        if self.name in kwargs:
            setattr(obj, self.name, kwargs.pop(self.name))
        elif not hasattr(obj, self.name):
            setattr(obj, self.name, copy_if_supported(self.default))
    
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "%s=%s" % (self.name, super(Field, self).to_repr(obj, context))

    def get_value(self, obj):
        return getattr(obj, self.name, self.default)

    def set_value(self, obj, value):
        setattr(obj, self.name, value)

    def __str__(self):
        return "field %s" % self.name

class FieldListContainer(FieldMarshal):
    def __init__(self, fields):
        super(FieldListContainer, self).__init__()
        self.fields = fields

    def prepare_class(self, cls):
        for field in self.fields:
            field.prepare_class(cls)

    def prepare_instance(self, obj, args, kwargs):
        for field in self.fields:
            field.prepare_instance(obj, args, kwargs)

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        for field in self.fields:
            field.read_fields(obj, stream, context, *args, **kwargs)

    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        for field in self.fields:
            field.write_fields(obj, stream, context)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return ", ".join([ field.to_repr(obj, context) for field in self.fields ])

    def sizeof(self, obj):
        return sum([ field.sizeof(obj) for field in self.fields ])

    def min_max_sizeof(self):
        return sum([ field.min_max_sizeof() for field in self.fields ], ZERO_MIN_MAX)

class StructType(type):
    def __new__(cls, name, bases, attrs):
        # If we initialize our own class don't do any modifications.
        if name == "Struct":
            return super(StructType, cls).__new__(cls, name, bases, attrs)

        # We want to first put our own __init__ method that will initialize all the fields passed by kwargs and then
        # call the user's __init__ method (if exists) with args/kwargs left.
        if "__init__" in attrs:
            user_init = attrs["__init__"]
            del attrs["__init__"]
        else:
            user_init = None

        new_cls = super(StructType, cls).__new__(cls, name, bases, attrs)

        # We wait for the class to be created to check the fields, because we want to take advantage of Python's MRO
        # to resolve the _fields_ structure.
        if not hasattr(new_cls, "_fields_"):
            raise StructNotWellDefinedError("Class %s is missing a _fields_ declaration" % (name,))

        fields = getattr(new_cls, "_fields_")
        
        if isinstance(fields, (types.ListType, types.TupleType)):
            fields = FieldListContainer(fields)

        setattr(new_cls, "_container_", fields)

        fields.prepare_class(new_cls)

        setattr(new_cls, "__init__", cls._create_struct_class_init(new_cls, user_init))
        return new_cls

    @classmethod
    def _create_struct_class_init(cls, new_cls, user_init):
        def __instance_init__(self, *args, **kwargs):
            orig_kwargs = kwargs.copy()
            if type(self) == new_cls:
                # Only do our magic if we're the bottom-most class.
                new_cls._container_.prepare_instance(self, args, kwargs)
            if user_init is None:
                super(new_cls, self).__init__(*args, **kwargs)
            else:
                # Add arguments back if the user code wants them.
                # This solves STORAGEMODEL-146, because ASI defines Read10Command(logical_block_address, ...)
                # and logical_block_address is also a field in the struct, so in this scenario instruct will
                # "eat" the arg and we need to put it back.
                for arg in user_init.func_code.co_varnames[0:user_init.func_code.co_argcount]:
                    if arg in orig_kwargs:
                        kwargs[arg] = orig_kwargs[arg]
                user_init(self, *args, **kwargs)
        return __instance_init__

class Struct(object):
    __metaclass__ = StructType

    def __init__(self, *args, **kwargs):
        super(Struct, self).__init__()
        type(self)._container_.prepare_instance(self, args, kwargs)
        
    @classmethod
    def write_to_stream(cls, obj, stream, context=EMPTY_CONTEXT):
        context = cls.get_updated_context(obj, context)
        type(obj)._container_.write_fields(obj, stream, context)

    @classmethod
    def create_from_stream(cls, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = cls(*args, **kwargs)
        context = cls.get_updated_context(obj, context)
        cls._container_.read_fields(obj, stream, context, *args, **kwargs)
        return obj

    @classmethod
    def min_max_sizeof(cls):
        return cls._container_.min_max_sizeof()
    
    @classmethod
    def sizeof(cls, obj):
        return cls._container_.sizeof(obj)

    @classmethod
    def write_to_string(cls, obj, context=EMPTY_CONTEXT):
        stream = StringIO()
        type(obj).write_to_stream(obj, stream, context)
        result = stream.getvalue()
        stream.close()
        return result

    @classmethod
    def create_from_string(cls, str, context=EMPTY_CONTEXT, *args, **kwargs):
        stream = StringIO(str)
        obj = cls.create_from_stream(stream, context, *args, **kwargs)
        stream.close()
        return obj

    @classmethod
    def to_repr(cls, obj, context=EMPTY_CONTEXT):
        if obj is None:
            return "<none>"
        cls = type(obj)
        context = cls.get_updated_context(obj, context)
        return("%s(%s)" % (cls.__name__, cls._container_.to_repr(obj, context)))

    @classmethod
    def get_updated_context(cls, obj, context):
        cls = type(obj)
        if hasattr(cls, '_context_'):
            new_context = WritableContext(cls._context_.copy())
        else:
            new_context = WritableContext(dict(struct=obj))
        new_context.update(context.get_dict())
        return new_context

    def __str__(self):
        return type(self).write_to_string(self)

    def __repr__(self):
        return type(self).to_repr(self)
