from cStringIO import StringIO

class SerializerBase(object):
    """
    This is the heart of serializing data to/from a stream.
    A serializer is responsible for:
    - reading/writing an object from/to a stream
    - calculating the size in bytes of an object
    - pretty printing the object
    """
    def min_sizeof(self):
        """
        Returns the minimum size in bytes an object will require.
        """
        raise NotImplementedError("BUG: min_sizeof is not implemented for class %s" % type(self))

    def sizeof(self, obj):
        """
        Calculate the actual size in bytes of an object.
        """
        raise NotImplementedError("BUG: sizeof is not implemented for class %s" % type(self))

    def is_fixed_size(self):
        """
        Returns True if the object is fixed-size, False if not.
        """
        raise NotImplementedError("BUG: is_fixed_size is not implemented for class %s" % type(self))

    def validate(self, obj):
        """
        Validates the object to be serialized and raises an exception if a serialization error will occur.
        """
        pass

    def to_repr(self, obj):
        """
        Returns a printable representation of the object or object.
        """
        raise NotImplementedError("BUG: to_repr is not implemented for class %s" % type(self))

    def write_to_stream(self, obj, stream):
        """
        Writes the instance to the stream.
        """
        raise NotImplementedError("BUG: write_to_stream is not implemented for class %s" % type(self))

    def to_string(self, obj):
        """
        Serializes the object and returns the serialized string.
        This is a convenience method that creates a StringIO object and calls write_instance_to_stream().
        """
        io = StringIO()
        self.write_to_stream(obj, io)
        result = io.getvalue()
        io.close()
        return result

class CreatorSerializer(SerializerBase):
    """
    This serializer creates a new object from a stream. This is targeted for immutable objects such as primitives.
    """
    def create_from_stream(self, stream, *args, **kwargs):
        """
        Creates a new instance and sets its attributes by reading the stream.
        The extra args and kwargs are passed to the instance's constructor so transient information can be passed
        on instance creation.
        """
        raise NotImplementedError()

    def create_from_string(self, string, *args, **kwargs):
        """
        Deserializes a new instance from a string.
        This is a convenience method that creates a StringIO object and calls create_instance_from_stream().
        """
        io = StringIO(string)
        instance = self.create_from_stream(io, *args, **kwargs)
        io.close()
        return instance

class ModifierSerializer(SerializerBase):
    """
    This serializer modifies an existing object by reading attributes from a stream. This is targeted for mutable
    objects such as classes/structs.
    """
    def read_into_from_stream(self, obj, stream):
        """
        Reads attributes into obj from the stream.
        """
        raise NotImplementedError()

    def read_into_from_string(self, obj, string):
        """
        Reads attributes into obj from a string.
        This is a convenience method that creates a StringIO object and calls read_into_from_stream().
        """
        io = StringIO(string)
        instance = self.read_into_from_stream(obj, io)
        io.close()

class MutableObjectSerializer(CreatorSerializer, ModifierSerializer):
    def __init__(self, factory):
        self.factory = factory

    def create_from_stream(self, stream, *args, **kwargs):
        obj = self.factory(*args, **kwargs)
        self.read_into_from_stream(obj, stream)
        return obj

class AggregateModifierSerializer(ModifierSerializer):
    def __init__(self, serializers):
        self.serializers = serializers
        self.all_fixed_size = all(map(lambda serializer: serializer.is_fixed_size(), serializers))
        self.min_size = reduce(lambda s, serializer: s + serializer.min_sizeof(), self.serializers, 0)
    
    def min_sizeof(self):
        return self.min_size

    def sizeof(self, obj):
        if self.all_fixed_size:
            return self.min_size
        return reduce(lambda s, serializer: s + serializer.sizeof(obj), self.serializers, 0)

    def is_fixed_size(self): 
        self.all_fixed_size

    def validate(self, obj):
        for serializer in self.serializers:
            serializer.validate(obj)

    def to_repr(self, obj):
        return ", ".join([ serializer.to_repr(obj) for serializer in self.serializers ])
    
    def write_to_stream(self, obj, stream):
        for serializer in self.serializers:
            serializer.write_to_stream(obj, stream)

    def read_into_from_stream(self, obj, stream):
        for serializer in self.serializers:
            serializer.read_into_from_stream(obj, stream)

class FixedSizeSerializerMixin(object):
    """
    Convenience class for fixed-size fields.
    """
    def is_fixed_size(self):
        return True

    def min_sizeof(self):
        return self.size

    def sizeof(self, instance):
        return self.size
