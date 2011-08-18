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

class PositionalBitMarshal(FixedSizer, Marshal):
    def __init__(self, slices):
        super(PositionalBitMarshal, self).__init__()
        self.slices = slices
        self.size = sum([ s.stop - s.start for s in slices ])

    def get_slices(self):
        return self.slices

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        value = 0
        bits = 0
        for s in self.slices:
            stream.seek(s.start)
            slice_size = s.stop - s.start
            value += stream.read(slice_size) << bits
            bits += slice_size
        return value

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        for s in self.slices:
            stream.seek(s.start)
            slice_size = s.stop - s.start
            stream.write(obj & ((1 << slice_size) - 1), slice_size)
            obj >>= slice_size

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return context.get('int_repr_format', '%d') % obj

class PositionalBitFieldListContainer(FixedSizer, FieldListContainer):
    def __init__(self, bit_size, fields):
        super(PositionalBitFieldListContainer, self).__init__(fields)
        if not all([ field.is_fixed_size() for field in self.fields ]):
            raise InstructError("all fields in a bit field list must be fixed size")

        field_bit_size = max([ max([ s.stop for s in field.marshal.get_slices() ]) for field in self.fields ])
        if bit_size is None:
            bit_size = field_bit_size

        if bit_size < field_bit_size:
            raise ValueError("bit size is set to %d but the fields index max bit %d" % (bit_size, field_bit_size))

        self.bit_size = bit_size
        if (self.bit_size % 8) != 0:
            raise BitFieldNotInByteBoundry()
        
        self.size = self.bit_size / 8
        
    def write_fields(self, obj, stream, context=EMPTY_CONTEXT):
        bit_stream = BitStringIO(self.size)
        for field in self.fields:
            field.write_fields(obj, bit_stream, context)
        stream.write(bit_stream.getvalue())

    def read_fields(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        bit_stream = BitStringIO(stream.read(self.size))
        for field in self.fields:
            field.read_fields(obj, bit_stream, context, *args, **kwargs)
