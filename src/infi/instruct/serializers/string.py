import struct
from ..serializer import DynamicSerializer
from ..errors import InvalidValueError

class FixedSizeStringSerializer(DynamicSerializer):
    def __init__(self, size):
        super(FixedSizeStringSerializer, self).__init__()
        self.size = size
        
    def create_instance_from_stream(self, stream, *args, **kwargs):
        string = stream.read(self.size)
        return struct.unpack("%ds" % self.size, string)[0]

    def write_instance_to_stream(self, instance, stream):
        if len(instance) > self.size:
            raise InvalidValueError("fixed-size string length is expected to be of length %d or smaller but instead got %d (string=%s)" % (self.size, len(instance), repr(instance)))
        stream.write(struct.pack("%ds" % self.size, instance))

    def sizeof(self):
        return self.size
