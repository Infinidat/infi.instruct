class StructTypeAdapter(object):
    def __init__(self, buffer_type):
        self.buffer_type = buffer_type

    def create_from_string(self, s):
        buf = self.buffer_type()
        buf.unpack(s)
        return buf

    def write_to_stream(self, *args):
        raise NotImplementedError()

    def create_from_stream(self, *args, **kwargs):
        raise NotImplementedError()

    def min_max_sizeof(self):
        raise NotImplementedError()

    def sizeof(self, obj):
        raise NotImplementedError()

    def write_to_string(self, *args, **kwargs):
        raise NotImplementedError()

    def to_repr(self, *args, **kwargs):
        raise NotImplementedError()

    def get_updated_context(self, *args, **kwargs):
        raise NotImplementedError()


def buffer_to_struct_adapter(buffer_type):
    return StructTypeAdapter(buffer_type)
