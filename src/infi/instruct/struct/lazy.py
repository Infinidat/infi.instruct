from cStringIO import StringIO

from . import FieldBase, Field, FieldListContainer
from ..base import FixedSizer, EMPTY_CONTEXT

class LazyField(Field):
    def __init__(self, container, field):
        super(LazyField, self).__init__(field.name, field.default, field.marshal)
        self.container = container
        self.field = field

    def prepare_class(self, cls):
        setattr(cls, self.field.name, self)

    def prepare_instance(self, obj, args, kwargs):
        if self.name in kwargs:
            setattr(obj, self.name, kwargs.pop(self.name))
        
    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        self.field.write_fields(obj, stream, context)

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        self.field.read_fields(obj, stream, context, *args, **kwargs)
        
    def __set__(self, instance, value):
        self.container.instantiate_if_needed(instance)
        instance.__dict__[self.name] = value
    
    def __get__(self, instance, owner):
        self.container.instantiate_if_needed(instance)
        return instance.__dict__[self.name]

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        if self.container.is_instantiated(obj):
            return self.field.to_repr(obj, context)
        return "<lazy>"

    def sizeof(self, obj):
        return self.field.sizeof(obj)

    def min_max_sizeof(self):
        return self.field.min_max_sizeof()

class LazyFieldListContainer(FixedSizer, FieldListContainer):
    def __init__(self, fields):
        new_fields = []
        for field in fields:
            if not field.is_fixed_size():
                raise ValueError("%s must be a fixed-size field inside a lazy container" % (field,))
            if isinstance(field, Field):
                new_fields.append(LazyField(self, field))
            else:
                new_fields.append(field)
        
        super(LazyFieldListContainer, self).__init__(new_fields)

        self.size = sum([ field.min_max_sizeof().min for field in self.fields ])
        self.lazy_key = "_lazy_container_%s" % id(self)

    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        self.instantiate_if_needed(obj)
        super(LazyFieldListContainer, self).write_fields(obj, stream)

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        data = stream.read(self.size)
        setattr(obj, self.lazy_key, dict(data=data, context=context, args=args, kwargs=kwargs))

    def is_instantiated(self, obj):
        return not hasattr(obj, self.lazy_key)

    def instantiate_if_needed(self, obj):
        if self.is_instantiated(obj):
            return

        params = getattr(obj, self.lazy_key)
        stream = StringIO(params['data'])

        # We first delete the lazy key so it'll return "instantiated" when the field descriptors are called.
        delattr(obj, self.lazy_key)
        
        super(LazyFieldListContainer, self).read_fields(obj, stream, params['context'], *params['args'],
                                                        **params['kwargs'])
