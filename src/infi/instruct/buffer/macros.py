from functools import partial
from infi.instruct.utils.kwargs import keep_kwargs_partial
from infi.instruct.utils.safe_repr import safe_repr

from .reference import (Reference, ContextGetAttrReference, FuncCallReference, LengthFuncCallReference,
                        TotalSizeReference, AfterFieldReference, FieldOrAttrReference, SelfProxy, ByteRangeFactory,
                        NumericCastReference, InputBufferLengthReference, MinFuncCallReference, MaxFuncCallReference)
from .field_reference_builder import FieldReferenceBuilder

from .buffer import BufferType

from .serialize import (pack_int, unpack_int, pack_float, unpack_float, pack_str, unpack_str, pack_bytearray,
                        unpack_bytearray, pack_buffer, unpack_buffer, pack_list, unpack_list, pack_json, unpack_json)

__all__ = [
    'int8', 'n_int8', 'b_int8', 'l_int8', 'uint8', 'n_uint8', 'b_uint8', 'l_uint8',
    'int16', 'n_int16', 'b_int16', 'l_int16', 'uint16', 'n_uint16', 'b_uint16', 'l_uint16',
    'int32', 'n_int32', 'b_int32', 'l_int32', 'uint32', 'n_uint32', 'b_uint32', 'l_uint32',
    'int64', 'n_int64', 'b_int64', 'l_int64', 'uint64', 'n_uint64', 'b_uint64', 'l_uint64',
    'int_field', 'uint_field', 'float_field', 'str_type', 'str_type_factory', 'str_field', 'buffer_field', 'list_field',
    'bytearray_field', 'be_int_field', 'le_int_field', 'bytes_ref', 'total_size', 'after_ref', 'member_func_ref',
    'le_uint_field', 'be_uint_field', 'len_ref', 'min_ref', 'max_ref', 'self_ref', 'num_ref', 'input_buffer_length',
    'json_field'
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
self_ref = SelfProxy()
input_buffer_length = InputBufferLengthReference()


def str_type_factory(encoding='ascii', padding=' ', strip='\x00', justify='left', byte_size=None):
    kwargs = dict(encoding=encoding, padding=padding, strip=strip, justify=justify)
    if byte_size:
        kwargs['byte_size'] = byte_size
    return (keep_kwargs_partial(pack_str, **kwargs), keep_kwargs_partial(unpack_str, **kwargs))

str_type = str_type_factory()


def int_field(endian='native', sign='signed',
              set_before_pack=None,
              set_after_unpack=None,
              pack_if=True,
              unpack_if=True,
              where=None,
              where_when_pack=None,
              where_when_unpack=None,
              unpack_after=None,
              byte_size=None,
              default=None):
    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
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


def uint_field(*args, **kwargs):
    kwargs.update(sign='unsigned')
    return int_field(*args, **kwargs)


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
                pack_if=True,
                unpack_if=True,
                where=None,
                where_when_pack=None,
                where_when_unpack=None,
                unpack_after=None,
                byte_size=None,
                default=None):
    builder = FieldReferenceBuilder(numeric=True,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
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
                    pack_if=None,
                    unpack_if=None,
                    where=None,
                    where_when_pack=None,
                    where_when_unpack=None,
                    unpack_after=None,
                    default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    builder.set_packer(pack_bytearray)
    builder.set_unpacker(unpack_bytearray)
    return builder.create()


def str_field(encoding='ascii', padding=' ', strip='\x00', justify='left',
              set_before_pack=None,
              set_after_unpack=None,
              pack_if=None,
              unpack_if=None,
              where=None,
              where_when_pack=None,
              where_when_unpack=None,
              unpack_after=None,
              default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    marshal_kwargs = dict(encoding=encoding, padding=padding, strip=strip, justify=justify)
    builder.set_packer(pack_str, **marshal_kwargs)
    builder.set_unpacker(unpack_str, **marshal_kwargs)
    return builder.create()


def json_field(set_before_pack=None,
               set_after_unpack=None,
               pack_if=None,
               unpack_if=None,
               where=None,
               where_when_pack=None,
               where_when_unpack=None,
               unpack_after=None,
               default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
                                    where=where,
                                    where_when_pack=where_when_pack,
                                    where_when_unpack=where_when_unpack,
                                    unpack_after=unpack_after,
                                    default=default)
    marshal_kwargs = dict(encoding='ascii', padding=' ', strip='\x00', justify='left',)
    builder.set_packer(pack_json, **marshal_kwargs)
    builder.set_unpacker(unpack_json, **marshal_kwargs)
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
    return FuncCallReference(False, partial, my_selector, ContextGetAttrReference(False, 'obj'))


def buffer_field(type,
                 unpack_selector=None,
                 set_before_pack=None,
                 set_after_unpack=None,
                 pack_if=None,
                 unpack_if=None,
                 where=None,
                 where_when_pack=None,
                 where_when_unpack=None,
                 unpack_after=None,
                 byte_size=None,
                 default=None):
    builder = FieldReferenceBuilder(numeric=False,
                                    set_before_pack=set_before_pack,
                                    set_after_unpack=set_after_unpack,
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
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
               pack_if=None,
               unpack_if=None,
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
                                    pack_if=pack_if,
                                    unpack_if=unpack_if,
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


def after_ref(field_ref):
    return AfterFieldReference(field_ref)


def member_func_ref(func):
    return FuncCallReference(False, func, ContextGetAttrReference(False, 'obj'))


def len_ref(ref_or_str):
    return LengthFuncCallReference(_make_field_ref(ref_or_str))


def num_ref(ref):
    return NumericCastReference(ref)


def min_ref(*refs):
    return MinFuncCallReference(*refs)


def max_ref(*refs):
    return MaxFuncCallReference(*refs)


def _make_field_ref(ref_or_str):
    if isinstance(ref_or_str, Reference):
        return ref_or_str
    else:
        # Note that we can't determine whether the attribute is numeric or not at this stage - it will require a
        # second pass to understand that, so we say it's not numeric and the user will have to use num_ref() to cast it
        # as numeric if needed.
        return FieldOrAttrReference(False, ref_or_str)
