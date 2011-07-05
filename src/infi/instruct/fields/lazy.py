from StringIO import StringIO
from . import Field, NamedField, PlainFieldContainer

class LazyFieldDecorator(NamedField):
    def __init__(self, container, field):
        self.container = container
        self.field = field
        self.name = field.name

    def write_to_stream(self, instance, stream):
        self.field.write_to_stream(instance, stream)

    def read_from_stream(self, instance, stream):
        self.field.read_from_stream(instance, stream)
        
    def __set__(self, instance, value):
        self.container.instantiate_if_needed(instance)
        self.field.__set__(instance, value)
    
    def __get__(self, instance, owner):
        self.container.instantiate_if_needed(instance)
        return self.field.__get__(instance, owner)

    def instance_repr(self, instance):
        if self.container.is_instantiated(instance):
            return self.field.instance_repr(instance)
        return "<lazy>"
    
    def sizeof(self):
        return self.field.sizeof()
    
class LazyFieldContainer(PlainFieldContainer):
    def __init__(self, fields):
        # Decorate all the named fields.
        decorated_fields = []
        size = 0
        for field in fields:
            field_size = field.sizeof()
            if field_size is None:
                raise ValueError("%s is not a fixed-size field inside a lazy container" % field)
            size += field_size
            if isinstance(field, NamedField):
                decorated_fields.append(LazyFieldDecorator(self, field))
            else:
                decorated_fields.append(field)
        
        super(LazyFieldContainer, self).__init__(decorated_fields)

        self.size = size
        self.lazy_key = "_lazy_container_%s" % id(self)

    def write_to_stream(self, instance, stream):
        self.instantiate_if_needed(instance)
        super(LazyFieldContainer, self).write_to_stream(instance, stream)

    def read_from_stream(self, instance, stream):
        data = stream.read(self.size)
        instance._values_[self.lazy_key] = dict(instantiated=False, data=data)

    def is_instantiated(self, instance):
        return self.lazy_key not in instance._values_

    def instantiate_if_needed(self, instance):
        if self.is_instantiated(instance):
            return
        io = StringIO(instance._values_[self.lazy_key]['data'])
        for field in self.fields:
            field.read_from_stream(instance, io)
        del instance._values_[self.lazy_key]

    def sizeof(self):
        return self.size

    def min_sizeof(self):
        return self.size
