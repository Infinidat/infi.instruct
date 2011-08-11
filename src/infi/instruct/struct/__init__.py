import types
from infi.exceptools import chain

from ..base import MutatingReader, Writer, ReprCapable, EMPTY_CONTEXT, Sizer, ApproxSizer, is_sizer, is_approx_sizer
from ..base import is_repr_capable, MinMax
from ..mixin import install_mixin_if
from ..errors import InstructError, StructNotWellDefinedError

def copy_if_supported(obj):
    return obj.copy() if hasattr(obj, 'copy') else obj

class FieldAdapter(MutatingReader, Writer, ReprCapable):
    def __init__(self, name, default, io):
        super(FieldAdapter, self).__init__()
        self.name = name
        self.default = default
        self.io = io
        install_mixin_if(self, Sizer, is_sizer(self.io))
        install_mixin_if(self, ApproxSizer, is_approx_sizer(self.io))

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        value = getattr(obj, self.name, None)
        to_repr = self.io.to_repr if is_repr_capable(self.io) else repr
        return "%s=%s" % (self.name, to_repr(value) if value is not None else "<not set>")

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        try:
            value = self.io.create_from_stream(stream, *args, **kwargs)
        except InstructError, e:
            raise chain(InstructError("Error occurred while reading field '%s' for class %s" % (self.name, type(obj))))

        setattr(obj, self.name, value)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        value = getattr(obj, self.name, None)
        try:
            self.io.write_to_stream(value, stream)
        except InstructError, e:
            raise chain(InstructError("Error occurred while writing field '%s' for class %s" % (self.name, type(obj))))

    def prepare_instance(self, obj, args, kwargs):
        if self.name in kwargs:
            setattr(obj, self.name, kwargs.pop(self.name))
        elif not hasattr(obj, self.name):
            setattr(obj, self.name, copy_if_supported(self.default))

    # Conditional implementations (added only if sizer is a Sizer/ApproxSizer)
    def _Sizer_sizeof(self, obj, context=EMPTY_CONTEXT):
        return self.io.sizeof(obj, context)

    def _ApproxSizer_min_max_sizeof(self, context=EMPTY_CONTEXT):
        return self.io.min_max_sizeof(context)

class FieldListIO(MutatingReader, Writer, ReprCapable):
    def __init__(self, ios):
        super(FieldListIO, self).__init__()
        self.ios = ios
        self.min_max_size = None
        install_mixin_if(self, Sizer, all([ is_sizer(io) for io in self.ios ]))
        install_mixin_if(self, ApproxSizer, all([ is_approx_sizer(io) for io in self.ios ]))

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        for io in self.ios:
            io.read_into_from_stream(obj, stream, context, *args, **kwargs)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        for io in self.ios:
            io.write_to_stream(obj, stream, context)

    def prepare_class(self, cls):
        for io in [ io for io in self.ios if hasattr(io, 'prepare_class') ]:
            io.prepare_class(cls)

    def prepare_instance(self, obj, args, kwargs):
        # Called from the modified __init__ method of the class.
        # We made this a separate method so all the defaults will be initialized before the user's ctor is called.
        for io in [ io for io in self.ios if hasattr(io, 'prepare_instance') ]:
            io.prepare_instance(obj, args, kwargs)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "(" + ", ".join([ (io.to_repr(obj, context) if is_repr_capable(io) else repr(obj)) for io in self.ios ]) + ")"

    def _Sizer_sizeof(self, obj, context=EMPTY_CONTEXT):
        return sum([ io.sizeof(obj, context) for io in self.ios ])

    def _ApproxSizer_min_max_sizeof(self, context=EMPTY_CONTEXT):
        if self.min_max_size is None:
            self.min_max_size = MinMax(sum([ io.min_max_sizeof(context).min for io in self.ios ]),
                                       sum([ io.min_max_sizeof(context).max for io in self.ios ]))
        return self.min_max_size

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
            fields = FieldListIO(fields)

        setattr(new_cls, "_io_", fields)

        fields.prepare_class(new_cls)

        setattr(new_cls, "__init__", cls._create_struct_class_init(new_cls, user_init))
        return new_cls

    @classmethod
    def _create_struct_class_init(cls, new_cls, user_init):
        def __instance_init__(self, *args, **kwargs):
            if type(self) == new_cls:
                # Only do our magic if we're the bottom-most class.
                new_cls._io_.prepare_instance(self, args, kwargs)
            if user_init is None:
                super(new_cls, self).__init__(*args, **kwargs)
            else:
                user_init(self, *args, **kwargs)
        return __instance_init__

class Struct(object):
    __metaclass__ = StructType

    def __init__(self, *args, **kwargs):
        super(Struct, self).__init__()
        type(self)._io_.prepare_instance(self, args, kwargs)

    @classmethod
    def write_to_stream(cls, obj, stream, context=EMPTY_CONTEXT):
        type(obj)._io_.write_to_stream(obj, stream, context.writable_copy(dict(parent=obj)))

    @classmethod
    def create_from_string(cls, string, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = cls(*args, **kwargs)
        cls._io_.read_into_from_string(obj, string, context.writable_copy(dict(parent=obj)), *args, **kwargs)
        return obj

    @classmethod
    def create_from_stream(cls, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        obj = cls(*args, **kwargs)
        cls._io_.read_into_from_stream(obj, stream, context.writable_copy(dict(parent=obj)), *args, **kwargs)
        return obj

    @classmethod
    def min_max_sizeof(cls, context=EMPTY_CONTEXT):
        return cls._io_.min_max_sizeof(context)

    @classmethod
    def sizeof(cls, obj, context=EMPTY_CONTEXT):
        return cls._io_.sizeof(obj, context.writable_copy(dict(parent=obj)))

    @classmethod
    def write_to_string(cls, obj, context=EMPTY_CONTEXT):
        return type(obj)._io_.write_to_string(obj, context.writable_copy(dict(parent=obj)))

    @classmethod
    def to_repr(cls, obj, context=EMPTY_CONTEXT):
        return type(obj)._io_.to_repr(obj, context.writable_copy(dict(parent=obj)))

    def write_to_stream(self, stream, context=EMPTY_CONTEXT):
        type(self)._io_.write_to_stream(self, stream, context)

    def read_into_from_string(self, string, context=EMPTY_CONTEXT, *args, **kwargs):
        type(self)._io_.read_into_from_string(self, string, context, *args, **kwargs)

    def read_into_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        type(self)._io_.read_into_from_stream(self, stream, context, *args, **kwargs)

    def write_to_string(self, context=EMPTY_CONTEXT):
        return type(self)._io_.write_to_string(self, context.writable_copy(dict(parent=self)))

    def sizeof(self, context=EMPTY_CONTEXT):
        return type(self)._io_.sizeof(self, context)

    def __str__(self):
        return type(self)._io_.write_to_string(self)

    def __repr__(self):
        return self.to_repr()

    def to_repr(self, context=EMPTY_CONTEXT):
        cls = type(self)
        return("%s%s" % (cls.__name__, cls._io_.to_repr(self, context)))

    # Backward compatibility (0.10)
    # BEGIN DEPRECATION
    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    create_instance_from_stream = create_from_stream
    create_instance_from_string = create_from_string
    write_instance_to_stream = write_to_stream
    instance_to_string = write_to_string
    # END DEPRECATION
