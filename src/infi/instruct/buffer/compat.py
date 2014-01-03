class StructTypeAdapter(object):
    def __init__(self, buffer_type):
        self.buffer_type = buffer_type

    def create_from_string(self, s):
        buf = self.buffer_type()
        buf.unpack(s)
        return buf

    def write_to_stream(self, obj, stream, context=None):
        packed_data = obj.pack()
        stream.write(packed_data)

    def create_from_stream(self, stream, context=None, *args, **kwargs):
        if self.buffer_type.byte_size is not None:
            packed_data = stream.read(self.buffer_type.byte_size)
            result = self.buffer_type()
            result.unpack(packed_data)
            return result
        raise ValueError("cannot unpack a non-fixed size buffer")

    def min_max_sizeof(self):
        raise NotImplementedError()

    def sizeof(self, obj):
        return len(obj.pack())

    def write_to_string(self, obj, context=None):
        return obj.pack()

    def to_repr(self, obj, context=None):
        return repr(obj)

    def get_updated_context(self, *args, **kwargs):
        raise NotImplementedError()


def buffer_to_struct_adapter(buffer_type):
    return StructTypeAdapter(buffer_type)
