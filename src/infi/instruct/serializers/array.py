import struct
from ..errors import InstructError, NotEnoughDataError
from ..serializer import DynamicSerializer

class FixedSizeArraySerializer(DynamicSerializer):
    def __init__(self, n, serializer):
        self.n = n
        self.size = n * serializer.sizeof()
        self.elem_serializer = serializer

    def create_instance_from_stream(self, stream, *args, **kwargs):
        result = []
        for i in xrange(self.n):
            result.append(self.elem_serializer.create_instance_from_stream(stream, *args, **kwargs))
        return result

    def write_instance_to_stream(self, instance, stream):
        assert len(instance) == self.n
        for elem in instance:
            self.elem_serializer.write_instance_to_stream(elem, stream)

    def sizeof(self):
        return self.size
