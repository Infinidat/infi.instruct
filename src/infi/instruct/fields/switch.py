from . import Field, copy_if_supported
from ..errors import InstructError
from ..serializer import is_serializer, serializer_class

class MultiTypeSwitchSerializerNeededError(InstructError):
    pass

class MultiTypeSwitchField(Field):
    def __init__(self, name, predicate, serializer_options, default=None):
        super(MultiTypeSwitchField, self).__init__(name, None, default)
        self.predicate = predicate
        self.serializer_options = serializer_options
        for key, serializer in serializer_options.items():
            if not is_serializer(serializer):
                raise MultiTypeSwitchSerializerNeededError("value for option %s must be a serializer (e.g. Struct)" %
                                                           key)

        if default is not None and not is_serializer(default):
            raise MultiTypeSwitchSerializerNeededError("default value must be a serializer (e.g. Struct)")

    def write_to_stream(self, instance, stream):
        obj = self.__get__(instance, self.name)
        obj.write_instance_to_stream(obj, stream)

    def read_from_stream(self, instance, stream):
        serializer = self.serializer_options[self.predicate(instance, stream)]
        self.__set__(instance, serializer.create_instance_from_stream(stream))
    
    def instance_repr(self, instance):
        has_value = self.name in instance._values_
        value_str = None
        if not has_value and self.default is not None:
            value_str = "%s (default)" % self.default.instance_repr(self.default)
        elif not has_value:
            value_str = "<not set>"
        else:
            obj = instance._values_[self.name]
            value_str = obj.instance_repr(obj)
        return value_str

    def sizeof(self):
        return None

class DictSwitchField(MultiTypeSwitchField):
    def __init__(self, name, key_serializer, serializer_options, default=None):
        super(DictSwitchField, self).__init__(name, self._predicate, serializer_options,
                                              default)
        self.key_serializer = key_serializer
        
        if default is not None and not is_serializer(default):
            raise MultiTypeSwitchSerializerNeededError("default value must be a serializer (e.g. Struct)")

        self.value_type_to_serializer = {}
        for key, serializer in serializer_options.items():
            value_type = serializer_class(serializer)
            if value_type in self.value_type_to_serializer:
                raise DictSwitchField("key %s and key %s have the same serializer type" % (key,
                                                                            self.value_type_to_serializer[key][0]))
            self.value_type_to_serializer[value_type] = (key, serializer)

    def write_to_stream(self, instance, stream):
        obj = self.__get__(instance, self.name)
        obj_type = serializer_class(obj)
        key, serializer = self.value_type_to_serializer[obj_type]
        self.key_serializer.write_instance_to_stream(key, stream)
        serializer.write_instance_to_stream(obj, stream)
        
    def _predicate(self, instance, stream):
        return self.key_serializer.create_instance_from_stream(stream)
