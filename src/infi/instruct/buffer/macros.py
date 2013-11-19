from functools import partial
from ..utils.kwargs import keep_kwargs_partial
from .range import SequentialRangeList, ByteRangeFactory

from .reference import (safe_repr, Reference, Context, ContextGetAttrReference, ObjectReference, NumberReference,
                        GetAttrReference, SetAndGetAttrReference, NumericSetAndGetAttrReference,
                        FuncCallReference, NumericFuncCallReference, NumericGetAttrReference, NumericReference)

from .buffer import (BufferType, FieldReference, NumericFieldReference, PackAbsolutePositionReference,
                     UnpackAbsolutePositionReference, TotalSizeReference)

from .serialize import (pack_int, unpack_int, pack_float, unpack_float, pack_str, unpack_str, pack_bytearray,
                        unpack_bytearray, pack_buffer, unpack_buffer, pack_list, unpack_list)

__all__ = [
    'int8', 'n_int8', 'b_int8', 'l_int8', 'uint8', 'n_uint8', 'b_uint8', 'l_uint8',
    'int16', 'n_int16', 'b_int16', 'l_int16', 'uint16', 'n_uint16', 'b_uint16', 'l_uint16',
    'int32', 'n_int32', 'b_int32', 'l_int32', 'uint32', 'n_uint32', 'b_uint32', 'l_uint32',
    'int64', 'n_int64', 'b_int64', 'l_int64', 'uint64', 'n_uint64', 'b_uint64', 'l_uint64',
    'int_field', 'float_field', 'str_type', 'str_type_factory', 'str_field', 'buffer_field', 'list_field',
    'bytearray_field', 'be_int_field', 'le_int_field', 'bytes_ref', 'total_size', 'after_ref', 'member_func_ref',
    'le_uint_field', 'be_uint_field'
]
JUSTIFY = ('left', 'right')


def int_marshal(byte_size, sign, endian="native"):
    return (keep_kwargs_partial(pack_int, byte_size=byte_size, sign=sign, endian=endian),
            keep_kwargs_partial(unpack_int, byte_size=byte_size, sign=sign, endian=endian))

n_int8 = int8 = int_marshal(1, "signed", "native")
b_int8 = int_marshal(1, "signed", "big")
l_int8 = int_marshal(1, "signed", "little")

n_uint8 = uint8 = int_marshal(1, "unsigned", "native")
b_uint8 = int_marshal(1, "unsigned", "big")
l_uint8 = int_marshal(1, "unsigned", "little")

n_int16 = int16 = int_marshal(2, "signed", "native")
b_int16 = int_marshal(2, "signed", "big")
l_int16 = int_marshal(2, "signed", "little")

n_uint16 = uint16 = int_marshal(2, "unsigned", "native")
b_uint16 = int_marshal(2, "unsigned", "big")
l_uint16 = int_marshal(2, "unsigned", "little")

n_int32 = int32 = int_marshal(4, "signed", "native")
b_int32 = int_marshal(4, "signed", "big")
l_int32 = int_marshal(4, "signed", "little")

n_uint32 = uint32 = int_marshal(4, "unsigned", "native")
b_uint32 = int_marshal(4, "unsigned", "big")
l_uint32 = int_marshal(4, "unsigned", "little")

n_int64 = int64 = int_marshal(8, "signed", "native")
b_int64 = int_marshal(8, "signed", "big")
l_int64 = int_marshal(8, "signed", "little")

n_uint64 = uint64 = int_marshal(8, "unsigned", "native")
b_uint64 = int_marshal(8, "unsigned", "big")
l_uint64 = int_marshal(8, "unsigned", "little")

bytes_ref = ByteRangeFactory()
total_size = TotalSizeReference()


def str_type_factory(encoding='ascii', padding=' ', justify='left', byte_size=None):
    kwargs = dict(encoding=encoding, padding=padding, justify=justify)
    if byte_size:
        kwargs['byte_size'] = byte_size
    return (keep_kwargs_partial(pack_str, **kwargs), keep_kwargs_partial(unpack_str, **kwargs))

str_type = str_type_factory()


class InputBufferPartReference(Reference):
    def __init__(self, position_ref):
        self.position_ref = position_ref

    def evaluate(self, ctx):
        return ctx.input_buffer.get(self.position_ref(ctx))

    def __safe_repr__(self):
        return "input_buffer[{0!r}]".format(self.position_ref)


class UnpackerReference(FuncCallReference):
    def __init__(self, unpacker, absolute_position_ref, *args, **kwargs):
        super(UnpackerReference, self).__init__(unpacker, InputBufferPartReference(absolute_position_ref),
                                                *args, **kwargs)

    def _args_repr(self):
        return ", ".join(["buffer", "position"] + [safe_repr(arg) for arg in self.arg_refs[2:]])


class FieldUnpackerReference(Reference):
    def __init__(self, unpacker_ref):
        self.unpacker_ref = unpacker_ref

    def evaluate(self, ctx):
        return self.unpacker_ref.evaluate(ctx)[0]

    def __safe_repr__(self):
        return "field_unpack({0})".format(self.unpacker_ref._func_repr())


class NumericFieldUnpackerReference(FieldUnpackerReference, NumericReference):
    pass


class SequentialRangeListByteLengthReference(NumericFuncCallReference):
    def __init__(self, arg):
        super(SequentialRangeListByteLengthReference, self).__init__(SequentialRangeList.byte_length, arg)

    def __safe_repr__(self):
        return "byte_length_ref({0})".format(self._args_repr())


class PackSequentialRangeListByteLengthReference(SequentialRangeListByteLengthReference):
    """
    A short-circuit to make sure we don't end up in a cyclic reference if the packing position depends on the packing
    result.
    """
    def evaluate(self, ctx):
        if self.arg_refs[0].is_open(ctx):
            return None
        else:
            return super(PackSequentialRangeListByteLengthReference, self).evaluate(ctx)

    def __safe_repr__(self):
        return "pack_byte_length_ref({0})".format(self._args_repr())


class FieldReferenceBuilder(object):
    def __init__(self, numeric, set_before_pack, set_after_unpack, where, where_when_pack, where_when_unpack,
                 unpack_after, default):
        self.numeric = numeric
        self.set_before_pack = set_before_pack
        self.set_after_unpack = set_after_unpack
        self.where = where
        self.where_when_pack = where_when_pack
        self.where_when_unpack = where_when_unpack
        self.unpack_after = unpack_after
        self.default = default
        self.pack_size = None
        self.unpack_size = None

        self.get_obj_from_ctx_ref = ContextGetAttrReference('obj')
        self.set_and_get_class = NumericSetAndGetAttrReference if self.numeric else SetAndGetAttrReference

        self.resolve_static_where()
        self.create_field()
        self.set_field_position()
        self.set_field_pack_value_ref()

    def resolve_static_where(self):
        def resolve_static_ref(ref):
            range_list = None
            if ref.is_static():
                range_list = ref(Context())
            return range_list.byte_length() if range_list is not None else None

        if self.where is not None:
            assert self.where_when_pack is None and self.where_when_unpack is None
            self.pack_size = self.unpack_size = resolve_static_ref(self.where)

        if self.where_when_pack is not None:
            assert self.where is None and self.where_when_unpack is not None
            self.pack_size = resolve_static_ref(self.where_when_unpack)

        if self.where_when_unpack is not None:
            assert self.where is None and self.where_when_pack is not None
            self.unpack_size = resolve_static_ref(self.where_when_unpack)

        if self.pack_size is not None and self.unpack_size is not None:
            assert self.pack_size == self.unpack_size

    def create_field(self):
        field_class = NumericFieldReference if self.numeric else FieldReference
        self.field = field_class()
        # When we first create a field reference we don't know the field name yet. When __new__ will get called
        # on Buffer, it will fill it in for us.
        self.field.attr_name_ref = ObjectReference(None)
        self.field.default = self.default

    def set_field_position(self):
        if self.where is not None:
            pack_position_ref = unpack_position_ref = self.where
        else:
            pack_position_ref = self.where_when_pack
            unpack_position_ref = self.where_when_unpack

        self.field.pack_absolute_position_ref = PackAbsolutePositionReference(self.field, pack_position_ref)
        self.field.unpack_absolute_position_ref = UnpackAbsolutePositionReference(self.field, unpack_position_ref)

    def set_packer(self, packer, **kwargs):
        pack_kwargs = dict(byte_size=PackSequentialRangeListByteLengthReference(self.field.pack_absolute_position_ref),
                           pack_size=self.pack_size)
        pack_kwargs.update(kwargs)
        self.field.pack_ref = FuncCallReference(packer, self.field.pack_value_ref, **pack_kwargs)

    def set_unpacker(self, unpacker, **kwargs):
        unpack_kwargs = dict(byte_size=SequentialRangeListByteLengthReference(self.field.unpack_absolute_position_ref),
                             unpack_size=self.unpack_size)
        unpack_kwargs.update(kwargs)

        self.field.unpack_ref = UnpackerReference(unpacker, self.field.unpack_absolute_position_ref, **unpack_kwargs)

    def create(self):
        self.set_field_unpack_value_ref()
        self.set_field_unpack_after()
        return self.field

    def set_field_pack_value_ref(self):
        if self.set_before_pack is not None:
            if not isinstance(self.set_before_pack, Reference):
                if callable(self.set_before_pack):
                    pack_value_class = NumericFuncCallReference if self.numeric else FuncCallReference
                    pack_value_ref = pack_value_class(self.set_before_pack, self.get_obj_from_ctx_ref)
                else:
                    pack_value_class = NumberReference if self.numeric else ObjectReference
                    pack_value_ref = pack_value_class(self.set_before_pack)
            else:
                pack_value_ref = self.set_before_pack
            self.field.pack_value_ref = self.set_and_get_class(self.get_obj_from_ctx_ref, self.field.attr_name_ref, pack_value_ref)
        else:
            getter_ref_class = NumericGetAttrReference if self.numeric else GetAttrReference
            self.field.pack_value_ref = getter_ref_class(self.get_obj_from_ctx_ref, self.field.attr_name_ref)

    def set_field_unpack_value_ref(self):
        if self.numeric:
            field_unpack_ref = NumericFieldUnpackerReference(self.field.unpack_ref)
        else:
            field_unpack_ref = FieldUnpackerReference(self.field.unpack_ref)
        if self.set_after_unpack is not None:
            if not isinstance(self.set_after_unpack, Reference):
                unpack_value_class = NumericFuncCallReference if self.numeric else FuncCallReference
                unpack_value_ref = unpack_value_class(self.set_after_unpack, field_unpack_ref)
        else:
            unpack_value_ref = self.set_and_get_class(self.get_obj_from_ctx_ref, self.field.attr_name_ref, field_unpack_ref)

        self.field.unpack_value_ref = unpack_value_ref

    def set_field_unpack_after(self):
        if self.unpack_after is None:
            self.unpack_after = []
        elif not isinstance(self.unpack_after, (list, tuple)):
            self.unpack_after = [self.unpack_after]

        for unpack_after_field in self.unpack_after:
            assert isinstance(unpack_after_field, FieldReference)

        self.field.unpack_after = self.unpack_after


def int_field(endian='native', sign='signed',
              set_before_pack=None,
              set_after_unpack=None,
              where=None,
              where_when_pack=None,
              where_when_unpack=None,
              unpack_after=None,
              byte_size=None,
              default=None):
    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)

    marshal_kwargs = dict(sign=sign, endian=endian)
    if byte_size:
        marshal_kwargs['byte_size'] = byte_size
    builder.set_packer(pack_int, **marshal_kwargs)
    builder.set_unpacker(unpack_int, **marshal_kwargs)
    return builder.create()


def be_uint_field(*args, **kwargs):
    kwargs.update(sign='unsigned')
    return be_int_field(*args, **kwargs)


def be_int_field(*args, **kwargs):
    kwargs.update(dict(endian='big'))
    return int_field(*args, **kwargs)


def le_uint_field(*args, **kwargs):
    kwargs.update(sign='unsigned')
    return le_int_field(*args, **kwargs)


def le_int_field(*args, **kwargs):
    kwargs.update(dict(endian='little'))
    return int_field(*args, **kwargs)


def float_field(endian='native',
                set_before_pack=None,
                set_after_unpack=None,
                where=None,
                where_when_pack=None,
                where_when_unpack=None,
                unpack_after=None,
                byte_size=None,
                default=None):
    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    marshal_kwargs = dict(endian=endian)
    if byte_size:
        marshal_kwargs['byte_size'] = byte_size
    builder.set_packer(pack_float, **marshal_kwargs)
    builder.set_unpacker(unpack_float, **marshal_kwargs)
    return builder.create()


def bytearray_field(set_before_pack=None,
                    set_after_unpack=None,
                    where=None,
                    where_when_pack=None,
                    where_when_unpack=None,
                    unpack_after=None,
                    default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    builder.set_packer(pack_bytearray)
    builder.set_unpacker(unpack_bytearray)
    return builder.create()


def str_field(encoding='ascii', padding=' ', justify='left',
              set_before_pack=None,
              set_after_unpack=None,
              where=None,
              where_when_pack=None,
              where_when_unpack=None,
              unpack_after=None,
              default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    marshal_kwargs = dict(encoding=encoding, padding=padding, justify=justify)
    builder.set_packer(pack_str, **marshal_kwargs)
    builder.set_unpacker(unpack_str, **marshal_kwargs)
    return builder.create()


def unpack_selector_decorator(selector):
    def my_selector(obj, buffer, *args, **kwargs):
        o = selector(obj, buffer, *args, **kwargs)
        if isinstance(o, BufferType):
            result = o()
            byte_size = result.unpack(buffer)
            return result, byte_size
        elif isinstance(o, (list, tuple)):
            assert len(o) == 2, "selector returned a list but not a (obj, byte_size)-kind of list"
            return o
        elif o is None:
            return None, 0
        else:
            assert False, "selector didn't return a Buffer type, a pair of (obj, byte_size) or None, instead it returned {0!r}".format(o)
    return FuncCallReference(partial, my_selector, ContextGetAttrReference('obj'))


def buffer_field(type,
                 unpack_selector=None,
                 set_before_pack=None,
                 set_after_unpack=None,
                 where=None,
                 where_when_pack=None,
                 where_when_unpack=None,
                 unpack_after=None,
                 byte_size=None,
                 default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    marshal_kwargs = dict(type=type)
    if byte_size:
        marshal_kwargs = dict(byte_size=byte_size)
    builder.set_packer(pack_buffer, **marshal_kwargs)
    unpack = unpack_selector_decorator(unpack_selector) if unpack_selector else unpack_buffer
    builder.set_unpacker(unpack, **marshal_kwargs)
    return builder.create()


def list_field(type, n=None, unpack_selector=None,
               set_before_pack=None,
               set_after_unpack=None,
               where=None,
               where_when_pack=None,
               where_when_unpack=None,
               unpack_after=None,
               default=None):
    assert isinstance(type, (tuple, BufferType)), \
        "list type argument must be one of the predefined types or a subclass of Buffer but instead it's {0}".format(type)

    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)

    shared_kwargs = dict(n=n)

    if isinstance(type, tuple):
        elem_packer, elem_unpacker = type
    else:
        elem_packer, elem_unpacker = (pack_buffer, partial(unpack_buffer, type=type))

    builder.set_packer(pack_list, elem_packer=elem_packer, **shared_kwargs)
    if unpack_selector:
        builder.set_unpacker(unpack_list, elem_unpacker=unpack_selector_decorator(unpack_selector), **shared_kwargs)
    else:
        builder.set_unpacker(unpack_list, elem_unpacker=elem_unpacker, **shared_kwargs)
    return builder.create()


class AfterFieldReference(Reference, NumericReference):
    def __init__(self, field_ref):
        self.field_ref = field_ref

    def evaluate(self, ctx):
        offset = None
        if ctx.is_pack():
            offset = SequentialRangeList(self.field_ref.pack_absolute_position_ref(ctx)).max_stop()
        else:
            # This is a bit more tricky, since unpack_absolute_position_ref returns the length for the rest of the
            # buffer if it contains an open range.
            if self.field_ref.unpack_absolute_position_ref.is_open(ctx):
                # It's an open range, so we need to limit it by checking the _actual_ byte size the field used to unpack.
                # Since all reference results are cached, we can ask the unpack result again w/o performance problems.
                _, byte_size = self.field_ref.unpack_ref(ctx)
                position_list = self.field_ref.unpack_absolute_position_ref.unpack_position_ref(ctx)
                # Since we want the "highest" byte, we need to sort the ranges.
                offset = position_list.sorted().byte_offset(byte_size)
            else:
                offset = self.field_ref.unpack_absolute_position_ref(ctx).max_stop()
        return offset

    def __safe_repr__(self):
        return "after({0})".format(self.field_ref.attr_name_ref(Context()))


def after_ref(field_ref):
    return AfterFieldReference(field_ref)


def member_func_ref(func):
    return FuncCallReference(func, ContextGetAttrReference('obj'))
