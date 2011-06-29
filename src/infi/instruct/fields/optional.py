from . import Field

class OptionalField(Field):
    def __init__(self, name, serializer, predicate, default=None):
        super(OptionalField, self).__init__(name, serializer, default)
        self.predicate = predicate

    def write_to_stream(self, instance, stream):
        value = self.__get__(instance, self.name)
        if value is not None:
            self.serializer.write_instance_to_stream(value, stream)

    def read_from_stream(self, instance, stream):
        if self.predicate(instance, stream):
            self.__set__(instance, self.serializer.create_instance_from_stream(stream))

    def sizeof(self):
        return None
