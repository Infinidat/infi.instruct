from infi.pyutils.mixin import install_mixin

from . import FieldListIO
from ..base import AllocatingReader, MutatingReader, Writer, ReprCapable, FixedSizer, MinMax, is_approx_sizer
from ..base import Sizer, FixedSizer, EMPTY_CONTEXT
from ..errors import InstructError, BitFieldNotInByteBoundry, FieldTypeNotSupportedError
from ..utils.bitstringio import BitStringIO

class BitIO(AllocatingReader, Writer, ReprCapable, FixedSizer):
    def __init__(self, size):
        super(BitIO, self).__init__()
        self.size = size

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return stream.read(self.size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(obj, self.size)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

class BitPaddingIO(MutatingReader, Writer, ReprCapable, FixedSizer):
    def __init__(self, size):
        super(BitPaddingIO, self).__init__()
        self.size = size

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        stream.read(self.size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(0, self.size)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "<%d bits padding>" % (self.size,)

class BitFieldListIO(FieldListIO):
    def __init__(self, ios):
        super(BitFieldListIO, self).__init__(ios)
        if not all([ is_approx_sizer(io) and io.is_fixed_size() for io in self.ios ]):
            raise InstructError("all fields in a bit field list must be fixed size")
        self.size = sum([ io.min_max_sizeof().min for io in self.ios ])
        if (self.size % 8) != 0:
            raise BitFieldNotInByteBoundry()
        self.size /= 8
        install_mixin(self, FixedSizer)
        
    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        bit_stream = BitStringIO(self.size)
        for io in self.ios:
            io.write_to_stream(obj, bit_stream, context)
        stream.write(bit_stream.getvalue())

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        bit_stream = BitStringIO(stream.read(self.size))
        for io in self.ios:
            io.read_into_from_stream(obj, bit_stream, context, *args, **kwargs)

    def _Sizer_sizeof(self, obj, context=EMPTY_CONTEXT):
        return self.size
