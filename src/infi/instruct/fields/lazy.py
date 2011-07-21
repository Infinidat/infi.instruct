from StringIO import StringIO
from . import FieldAdapter, FieldListSerializer

class LazyFieldDecorator(FieldAdapter):
    def __init__(self, container, field):
        super(LazyFieldDecorator, self).__init__(field.name, field.default, field.serializer)
        self.container = container
        self.field = field

    def write_to_stream(self, obj, stream):
        self.field.write_to_stream(obj, stream)

    def read_into_from_stream(self, obj, stream):
        self.field.read_into_from_stream(obj, stream)
        
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
    
class LazyFieldListSerializer(FieldListSerializer):
    def __init__(self, serializers):
        new_serializers = []
        for serializer in serializers:
            if not serializer.is_fixed_size():
                raise ValueError("%s is not a fixed-size field inside a lazy container" % (serializer,))
            if isinstance(serializer, FieldAdapter):
                new_serializers.append(LazyFieldDecorator(self, serializer))
            else:
                new_serializers.append(serializer)
        
        super(LazyFieldListSerializer, self).__init__(new_serializers)

        self.size = self.min_size
        self.lazy_key = "_lazy_container_%s" % id(self)

    def write_to_stream(self, obj, stream):
        self.instantiate_if_needed(obj)
        super(LazyFieldListSerializer, self).write_to_stream(obj, stream)

    def read_from_stream(self, obj, stream):
        data = stream.read(self.size)
        setattr(obj, self.lazy_key, data)

    def is_instantiated(self, obj):
        return hasattr(obj, self.lazy_key)

    def instantiate_if_needed(self, obj):
        if self.is_instantiated(obj):
            return
        io = StringIO(getattr(obj, self.lazy_key))
        for serializer in self.serializers:
            serializer.read_into_from_stream(obj, io)
        delattr(obj, self.lazy_key)
