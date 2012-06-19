from .range import SequentialRangeList, ByteRangeFactory
from .reference import Reference, Context, ContextGetAttrReference, ObjectReference
from .reference import GetAttrReference, SetAndGetAttrReference, NumericSetAndGetAttrReference
from .reference import NumericFuncCallReference, NumericGetAttrReference
from .buffer import FieldReference, NumericFieldReference
from .buffer import  PackAbsolutePositionReference, UnpackAbsolutePositionReference
from .buffer import TotalSizeReference
from .serialize import FillPacker, IntMarshal, FloatMarshal, INT_MARSHALS, FLOAT_MARSHALS
from .serialize import StringMarshal, FillStringMarshal, BufferMarshal
from .serialize import Int8Marshal, Int16Marshal, Int32Marshal, Int64Marshal, Float32Marshal, Float64Marshal
from .serialize import ListPacker, ListUnpacker
from .serialize import PackerReference, UnpackerReference, FillPackerReference

ENDIAN = ('little', 'big', 'native')
SIGN = ('signed', 'unsigned')
JUSTIFY = ('left', 'right')


bytes_ref = ByteRangeFactory()
total_size = TotalSizeReference()

class FieldReferenceBuilder(object):
    def __init__(self, numeric, set_before_pack, set_after_unpack, where, where_when_pack, where_when_unpack):
        self.numeric = numeric
        self.set_before_pack = set_before_pack
        self.set_after_unpack = set_after_unpack
        self.where = where
        self.where_when_pack = where_when_pack
        self.where_when_unpack = where_when_unpack
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

def int_field(endian='little', sign='unsigned',
              set_before_pack=None,
              set_after_unpack=None,
              where=None,
              where_when_pack=None,
              where_when_unpack=None):
    assert endian in ENDIAN
    assert sign in SIGN

    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack)
    builder.resolve_static_where()
    if builder.pack_size is not None:
        assert builder.pack_size in INT_MARSHALS
        builder.set_packer(INT_MARSHALS[builder.pack_size](sign, endian))
    else:
        builder.set_packer(IntMarshal(sign, endian))

    if builder.unpack_size is not None:
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
                where_when_unpack=None):
    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack)
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
              where_when_unpack=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack)
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

def field(type=None, unpack_selector=None,
          set_before_pack=None,
          set_after_unpack=None,
          where=None,
          where_when_pack=None,
          where_when_unpack=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack)
    if type is not None:
        assert unpack_selector is None
        marshal = BufferMarshal(type)
        builder.set_packer(marshal)
        builder.set_unpacker(marshal)
    else:
        # FIXME: implement
        raise NotImplementedError()

    return builder.create()

def list_field(type=None, n=None, selector=None,
               set_before_pack=None,
               set_after_unpack=None,
               where=None,
               where_when_pack=None,
               where_when_unpack=None):
    assert not (selector is not None and type is not None)

    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack)

    if type is not None:
        builder.set_packer(ListPacker(type, n))
        builder.set_unpacker(ListUnpacker(type, n))
    else:
        raise NotImplementedError()

    return builder.create()

int8 = Int8Marshal
int16 = Int16Marshal
int32 = Int32Marshal
int64 = Int64Marshal
float32 = Float32Marshal
float64 = Float64Marshal
