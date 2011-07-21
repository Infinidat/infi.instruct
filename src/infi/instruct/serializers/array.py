import struct
from ..errors import InstructError, NotEnoughDataError
from ..serializer import CreatorSerializer

class ArraySerializerBase(CreatorSerializer):
    def __init__(self, element_serializer):
        self.element_serializer = element_serializer

    def to_repr(self, array):
        return "[ " + ", ".join([ self.element_serializer.to_repr(elem) for elem in array ]) + " ]"

class FixedSizeArraySerializer(ArraySerializerBase):
    """
    Serializes an array with a fixed number of elements (although each element may be of var size)
    """
    def __init__(self, element_serializer, n):
        super(FixedSizeArraySerializer, self).__init__(element_serializer)
        self.n = n

    def create_from_stream(self, stream, *args, **kwargs):
        result = []
        for i in xrange(self.n):
            result.append(self.element_serializer.create_from_stream(stream, *args, **kwargs))
        return result

    def write_to_stream(self, obj, stream):
        assert len(obj) == self.n
        for elem in obj:
            self.element_serializer.write_to_stream(elem, stream)

    def min_sizeof(self):
        return self.n * self.element_serializer.min_sizeof()

    def is_fixed_size(self):
        return self.element_serializer.is_fixed_size()

    def sizeof(self, array):
        return reduce(lambda s, elem: s + self.element_serializer.sizeof(elem), array, 0)

    def validate(self, array):
        # TODO: implement
        pass

class TotalSizeArraySerializer(ArraySerializerBase):
    """
    Serializes an array in the form of <total array size in bytes>, <elem1>, <elem2>, ..., <elemN>
    """
    def __init__(self, size_serializer, element_serializer):
        super(TotalSizeArraySerializer, self).__init__(element_serializer)
        self.size_serializer = size_serializer

    def create_from_stream(self, stream, *args, **kwargs):
        result = []
        remaining_bytes = self.size_serializer.create_from_stream(stream)
        while remaining_bytes > 0:
            element = self.element_serializer.create_from_stream(stream, *args, **kwargs)
            remaining_bytes -= self.element_serializer.sizeof(element)
        assert remaining_bytes == 0
        return result

    def write_to_stream(self, array, stream):
        total_size = reduce(lambda s, obj: s + self.element_serializer.sizeof(obj), array, 0)
        self.size_serializer.write_to_stream(total_size, stream)
        for elem in array:
            self.element_serializer.write_to_stream(elem, stream)

    def validate(self, obj):
        # TODO: implement
        pass

    def is_fixed_size(self):
        return False

    def sizeof(self, obj):
        return self.size_serializer.min_sizeof() + reduce(lambda s, elem: s + self.element_serializer.sizeof(elem),
                                                          obj, 0)

    def min_sizeof(self):
        return self.size_serializer.min_sizeof()
