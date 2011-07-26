from .base import MutatingReader, Writer, FixedSizer, ReprCapable, EMPTY_CONTEXT

class BytePaddingIO(MutatingReader, Writer, FixedSizer):
    def __init__(self, size, char="\x00"):
        super(BytePaddingIO, self).__init__()
        self.size = size
        self.char = char
        assert len(self.char) == 1

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(self.char * self.size)

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        stream.read(self.size)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "<%d bytes padding>" % (self.size,)
