from .base import FixedSizer, Marshal, EMPTY_CONTEXT

class BytePaddingMarshal(FixedSizer, Marshal):
    def __init__(self, size, char="\x00"):
        super(BytePaddingMarshal, self).__init__()
        self.size = size
        self.char = char
        assert len(self.char) == 1

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(self.char * self.size)

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        stream.read(self.size)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "<%d bytes padding>" % (self.size,)
