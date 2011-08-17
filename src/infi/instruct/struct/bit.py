from . import FieldListContainer
from ..base import FixedSizer, Marshal, MinMax, EMPTY_CONTEXT
from ..errors import InstructError, BitFieldNotInByteBoundry, FieldTypeNotSupportedError
from ..utils.bitstringio import BitStringIO

class BitMarshal(FixedSizer, Marshal):
    def __init__(self, size):
        super(BitMarshal, self).__init__()
        self.size = size

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return stream.read(self.size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(obj, self.size)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return context.get('int_repr_format', '%d') % obj

class BitPaddingMarshal(BitMarshal):
    def __init__(self, size):
        super(BitPaddingMarshal, self).__init__(size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        stream.write(0, self.size)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return "<%d bits padding>" % (self.size,)

class BitFieldListContainer(FixedSizer, FieldListContainer):
    def __init__(self, fields):
        super(BitFieldListContainer, self).__init__(fields)
        if not all([ field.is_fixed_size() for field in self.fields ]):
            raise InstructError("all fields in a bit field list must be fixed size")
        self.size = sum([ field.min_max_sizeof().min for field in self.fields ])
        if (self.size % 8) != 0:
            raise BitFieldNotInByteBoundry()
        self.size /= 8
        
    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        bit_stream = BitStringIO(self.size)
        for io in self.fields:
            io.write_fields(obj, bit_stream, context)
        stream.write(bit_stream.getvalue())

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        bit_stream = BitStringIO(stream.read(self.size))
        for field in self.fields:
            field.read_fields(obj, bit_stream, context, *args, **kwargs)
