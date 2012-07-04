from .range import SequentialRangeList, ByteRangeFactory
from .reference import Reference, Context, ContextGetAttrReference, ObjectReference
from .reference import GetAttrReference, SetAndGetAttrReference, NumericSetAndGetAttrReference
from .reference import NumericFuncCallReference, NumericGetAttrReference
from .buffer import Buffer, BufferType, FieldReference, NumericFieldReference
from .buffer import PackAbsolutePositionReference, UnpackAbsolutePositionReference
from .buffer import TotalSizeReference
from .serialize import FillPacker, Packer, Unpacker, IntMarshal, FloatMarshal, INT_MARSHALS, FLOAT_MARSHALS
from .serialize import StringMarshal, FillStringMarshal, BufferMarshal
from .serialize import Int8Marshal, Int16Marshal, Int32Marshal, Int64Marshal, Float32Marshal, Float64Marshal
from .serialize import BitIntMarshal, ListPacker, ListUnpacker
from .serialize import PackerReference, UnpackerReference, FillPackerReference

__all__ = [ 'int8', 'int16', 'int32', 'int64', 'float32', 'float64', 'bytes_ref', 'total_size',
            'int_field', 'float_field', 'str_field', 'buffer_field', 'list_field' ]
ENDIAN = ('little', 'big', 'native')
SIGN = ('signed', 'unsigned')
JUSTIFY = ('left', 'right')

int8 = Int8Marshal
int16 = Int16Marshal
int32 = Int32Marshal
int64 = Int64Marshal
float32 = Float32Marshal
float64 = Float64Marshal
bytes_ref = ByteRangeFactory()
total_size = TotalSizeReference()

class FieldReferenceBuilder(object):
    def __init__(self, numeric, set_before_pack, set_after_unpack, where, where_when_pack, where_when_unpack,
                 unpack_after):
        self.numeric = numeric
        self.set_before_pack = set_before_pack
        self.set_after_unpack = set_after_unpack
        self.where = where
        self.where_when_pack = where_when_pack
        self.where_when_unpack = where_when_unpack
        self.unpack_after = unpack_after
        self.packer = None
        self.unpacker = None
        self.pack_size = None
        self.unpack_size = None

    def resolve_static_where(self):
        if self.where is not None:
            if self.where.is_static():
                range_list = self.where(Context())
                if range_list is not None:
                    self.pack_size = self.unpack_size = range_list.byte_length()

        if self.where_when_pack is not None:
            assert self.where is None and self.where_when_unpack is not None
            if self.where_when_pack.is_static():
                range_list = self.where_when_pack(Context())
                if range_list is not None:
                    self.pack_size = range_list.byte_length()

        if self.where_when_unpack is not None:
            if self.where_when_unpack.is_static():
                range_list = self.where_when_unpack(Context())
                if range_list is not None:
                    self.unpack_size = range_list.byte_length()

        if self.pack_size is not None and self.unpack_size is not None:
            assert self.pack_size == self.unpack_size

    def set_packer(self, packer):
        self.packer = packer

    def set_unpacker(self, unpacker):
        self.unpacker = unpacker

    def create(self):
        self.resolve_static_where()

        field_class = NumericFieldReference if self.numeric else FieldReference
        field = field_class()

        get_obj_from_ctx_ref = ContextGetAttrReference('obj')

        # When we first create a field reference we don't know the field name yet. When __new__ will get called
        # on Buffer, it will fill it in for us.
        field.attr_name_ref = ObjectReference(None)

        self._set_position_on_field(field)

        set_and_get_class = NumericSetAndGetAttrReference if self.numeric else SetAndGetAttrReference

        self._set_pack_value_on_field(field, get_obj_from_ctx_ref, set_and_get_class)
        self._set_packer_on_field(field)
        self._set_unpacker_on_field(field)
        self._set_unpack_value_on_field(field, get_obj_from_ctx_ref, set_and_get_class)
        self._set_unpack_after_on_field(field)
        return field

    def _set_position_on_field(self, field):
        if self.where is not None:
            pack_position_ref = unpack_position_ref = self.where
        else:
            pack_position_ref = self.where_when_pack
            unpack_position_ref = self.where_when_unpack

        field.pack_absolute_position_ref = PackAbsolutePositionReference(field, pack_position_ref)
        field.unpack_absolute_position_ref = UnpackAbsolutePositionReference(field, unpack_position_ref)

    def _set_pack_value_on_field(self, field, get_obj_from_ctx_ref, set_and_get_class):
        if self.set_before_pack is not None:
            if not isinstance(self.set_before_pack, Reference):
                pack_value_class = NumericFuncCallReference if self.numeric else FuncCallReference
                pack_value_ref = pack_value_class(self.set_before_pack, get_obj_from_ctx_ref)
            else:
                pack_value_ref = self.set_before_pack
            field.pack_value_ref = set_and_get_class(get_obj_from_ctx_ref, field.attr_name_ref, pack_value_ref)
        else:
            getter_ref_class = NumericGetAttrReference if self.numeric else GetAttrReference
            field.pack_value_ref = getter_ref_class(get_obj_from_ctx_ref, field.attr_name_ref)

    def _set_packer_on_field(self, field):
        if isinstance(self.packer, FillPacker):
            byte_length_ref = NumericFuncCallReference(SequentialRangeList.byte_length,
                                                       field.pack_absolute_position_ref)
            field.pack_ref = FillPackerReference(self.packer, byte_length_ref, field.pack_value_ref)
        else:
            field.pack_ref = PackerReference(self.packer, field.pack_value_ref)

    def _set_unpacker_on_field(self, field):
        field.unpack_ref = UnpackerReference(self.unpacker, field.unpack_absolute_position_ref)

    def _set_unpack_value_on_field(self, field, get_obj_from_ctx_ref, set_and_get_class):
        if self.set_after_unpack is not None:
            if not isinstance(self.set_after_unpack, Reference):
                unpack_value_class = NumericFuncCallReference if self.numeric else FuncCallReference
                unpack_value_ref = unpack_value_class(self.set_after_unpack, field.unpack_ref)
        else:
            unpack_value_ref = set_and_get_class(get_obj_from_ctx_ref, field.attr_name_ref, field.unpack_ref)

        field.unpack_value_ref = unpack_value_ref

    def _set_unpack_after_on_field(self, field):
        if self.unpack_after is None:
            self.unpack_after = []
        elif not isinstance(self.unpack_after, (list, tuple)):
            self.unpack_after = [ self.unpack_after ]

        for unpack_after_field in self.unpack_after:
            assert isinstance(unpack_after_field, FieldReference)

        field.unpack_after = self.unpack_after

class SelectorDecoratorUnpacker(Unpacker):
    def __init__(self, selector):
        self.selector = selector
        assert self.selector.func_code.co_argcount in xrange(1, 3)

    def unpack(self, ctx, buffer):
        if self.selector.func_code.co_argcount == 2:
            unpacker = self.selector(ctx.obj, buffer)
        else:
            unpacker = self.selector(ctx.obj)

        if isinstance(unpacker, BufferType):
            result = unpacker()
            byte_size = result.unpack(buffer)
            return result, byte_size
        elif isinstance(unpacker, Unpacker):
            return unpacker.unpack(ctx, buffer)
        raise ValueError("selector {0!r} returned an unpacker {1!r} that's not of type Buffer or Unpacker.".format(self.selector, type))

    def __repr__(self):
        return "{0}".format(self.selector)

def int_field(endian='little', sign='unsigned',
              set_before_pack=None,
              set_after_unpack=None,
              where=None,
              where_when_pack=None,
              where_when_unpack=None,
              unpack_after=None):
    assert endian in ENDIAN
    assert sign in SIGN

    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after)
    builder.resolve_static_where()
    if builder.pack_size is not None:
        if builder.pack_size < 1:
            builder.set_packer(BitIntMarshal(builder.pack_size))
        else:
            assert builder.pack_size in INT_MARSHALS
            builder.set_packer(INT_MARSHALS[builder.pack_size](sign, endian))
    else:
        builder.set_packer(IntMarshal(sign, endian))

    if builder.unpack_size is not None:
        if builder.pack_size < 1:
            builder.set_unpacker(BitIntMarshal(builder.unpack_size))
        else:
            assert builder.unpack_size in INT_MARSHALS
            builder.set_unpacker(INT_MARSHALS[builder.pack_size](sign, endian))
    else:
        builder.set_unpacker(IntMarshal(sign, endian))

    return builder.create()

def float_field(size=None, endian='little',
                set_before_pack=None,
                set_after_unpack=None,
                where=None,
                where_when_pack=None,
                where_when_unpack=None,
                unpack_after=None):
    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after)
    builder.resolve_static_where()

    if builder.pack_size is not None:
        assert builder.pack_size in FLOAT_MARSHALS
        builder.set_packer(FLOAT_MARSHALS[builder.pack_size](endian))
    else:
        builder.set_packer(FloatMarshal(endian))

    if builder.unpack_size is not None:
        assert builder.unpack_size in FLOAT_MARSHALS
        builder.set_unpacker(FLOAT_MARSHALS[builder.pack_size](endian))
    else:
        builder.set_unpacker(FloatMarshal(endian))

    return builder.create()

def str_field(encoding='ascii', pad_char=' ', justify='left',
              set_before_pack=None,
              set_after_unpack=None,
              where=None,
              where_when_pack=None,
              where_when_unpack=None,
              unpack_after=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after)
    builder.resolve_static_where()
    if builder.pack_size is not None:
        builder.set_packer(FillStringMarshal(justify=justify, padding=pad_char, encoding=encoding))
    else:
        builder.set_packer(StringMarshal(encoding=encoding))

    if builder.unpack_size is not None:
        builder.set_unpacker(FillStringMarshal(justify=justify, padding=pad_char, encoding=encoding))
    else:
        builder.set_unpacker(StringMarshal(encoding=encoding))

    return builder.create()

def buffer_field(type,
                 unpack_selector=None,
                 set_before_pack=None,
                 set_after_unpack=None,
                 where=None,
                 where_when_pack=None,
                 where_when_unpack=None,
                 unpack_after=None):
    assert type is not None
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after)

    marshal = BufferMarshal(type)
    builder.set_packer(marshal)

    if unpack_selector is not None:
        builder.set_unpacker(SelectorDecoratorUnpacker(unpack_selector))
    else:
        builder.set_unpacker(marshal)

    return builder.create()

def list_field(type, n=None, unpack_selector=None,
               set_before_pack=None,
               set_after_unpack=None,
               where=None,
               where_when_pack=None,
               where_when_unpack=None,
               unpack_after=None):
    assert type is not None
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after)

    marshal = BufferMarshal(type) if isinstance(type, BufferType) else type
    assert isinstance(marshal, Unpacker) and isinstance(marshal, (Packer, FillPacker))
    builder.set_packer(ListPacker(marshal, n))
    if unpack_selector is not None:
        builder.set_unpacker(ListUnpacker(SelectorDecoratorUnpacker(unpack_selector)))
    else:
        builder.set_unpacker(ListUnpacker(marshal, n))

    return builder.create()
