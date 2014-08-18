import math
import struct
import json

from .io_buffer import BitAwareByteArray, BitView
from .buffer import BufferType

from ..errors import InstructError
from ..utils.kwargs import (copy_defaults_and_override_with_kwargs, assert_kwarg_enum, copy_and_remove_kwargs,
                            keep_kwargs_partial)


def kwargs_fractional_byte_size(kwargs):
    byte_size = kwargs.get("byte_size", None)
    assert byte_size is None or ((byte_size >= 0) and (int(byte_size * 8) == byte_size * 8)), \
        "size can be unknown (None) or a non-negative fraction of 8 but instead got {0}".format(byte_size)
    return byte_size


def kwargs_int_byte_size(kwargs):
    byte_size = kwargs.get("byte_size", None)
    assert byte_size is None or ((byte_size >= 0) and (int(byte_size) == byte_size)), \
        "size can be unknown (None) or a non-negative integer but instead got {0}".format(byte_size)
    return byte_size


def assert_enum_argument(name, value, enum):
    assert value in enum, "argument {0} with value {1!r} is not one of {2!r}".format(name, value, enum)


class PackError(InstructError):
    MESSAGE = "{pack_ref!r} failed to pack {value!r}."

    def __init__(self, pack_ref, value):
        super(PackError, self).__init__(PackError.MESSAGE.format(pack_ref=pack_ref, value=value))


class UnpackError(InstructError):
    MESSAGE = "{unpack_ref!r} failed to unpack {buffer!r}."

    def __init__(self, unpack_ref, buffer):
        super(UnpackError, self).__init__(UnpackError.MESSAGE.format(unpack_ref=unpack_ref, buffer=buffer))


ENDIAN_NAME_TO_FORMAT = {'unspecified': '@', 'native': '=', 'big': '>', 'little': '<'}


#
# integer support
#


def pack_bit_int(value, byte_size, **kwargs):
    assert byte_size is not None
    result = BitAwareByteArray(bytearray(int(math.ceil(byte_size))), 0, byte_size)
    result[0:] = value
    return result


def format_from_struct_int_arguments(format_char, kwargs):
    args = copy_defaults_and_override_with_kwargs(dict(sign='signed', endian='native'), kwargs)
    assert_enum_argument('format_char', format_char, ('b', 'h', 'l', 'q'))
    assert_kwarg_enum(args, 'sign', ('signed', 'unsigned'))
    assert_kwarg_enum(args, 'endian', ENDIAN_NAME_TO_FORMAT.keys())
    format_char = format_char.lower() if args["sign"] == "signed" else format_char.upper()
    return "{0}{1}".format(ENDIAN_NAME_TO_FORMAT[args["endian"]], format_char)


def pack_struct_int(value, format_char, **kwargs):
    return struct.pack(format_from_struct_int_arguments(format_char, kwargs), value)

STRUCT_INT_PACKERS = {
    1: keep_kwargs_partial(pack_struct_int, format_char='b'),
    2: keep_kwargs_partial(pack_struct_int, format_char='h'),
    4: keep_kwargs_partial(pack_struct_int, format_char='l'),
    8: keep_kwargs_partial(pack_struct_int, format_char='q')
}


def pack_int(value, **kwargs):
    byte_size = kwargs_fractional_byte_size(kwargs)
    if byte_size in STRUCT_INT_PACKERS:
        return STRUCT_INT_PACKERS[byte_size](value, **kwargs)
    else:
        byte_size = kwargs.pop("byte_size", float(value.bit_length()) / 8)
        return pack_bit_int(value, byte_size, **kwargs)


def unpack_bit_int(buffer, byte_size, **kwargs):
    result = 0
    l = reversed(buffer[0:byte_size]) if kwargs.get("endian", "big") else buffer[0:byte_size]
    for b in l:
        result *= 256
        result += b
    return result, byte_size


def unpack_struct_int(buffer, format_char, **kwargs):
    format = format_from_struct_int_arguments(format_char, kwargs)
    byte_size = struct.calcsize(format)
    assert len(buffer) >= byte_size, "buffer size must be at least {0} but instead got {1}".format(byte_size, len(buffer))
    return struct.unpack(format, str(buffer[0:byte_size]))[0], byte_size

STRUCT_INT_UNPACKERS = {
    1: keep_kwargs_partial(unpack_struct_int, format_char='b'),
    2: keep_kwargs_partial(unpack_struct_int, format_char='h'),
    4: keep_kwargs_partial(unpack_struct_int, format_char='l'),
    8: keep_kwargs_partial(unpack_struct_int, format_char='q')
}


def unpack_int(buffer, **kwargs):
    byte_size = kwargs_fractional_byte_size(kwargs)
    if byte_size in STRUCT_INT_UNPACKERS:
        return STRUCT_INT_UNPACKERS[byte_size](buffer, **kwargs)
    else:
        byte_size = kwargs.pop('byte_size', buffer.length())
        return unpack_bit_int(buffer, byte_size, **kwargs)

#
# float support
#


def format_from_struct_float_arguments(format_char, kwargs):
    args = copy_defaults_and_override_with_kwargs(dict(endian='native'), kwargs)
    assert_enum_argument('format_char', format_char, ('f', 'd'))
    assert_kwarg_enum(args, 'endian', ENDIAN_NAME_TO_FORMAT.keys())
    return "{0}{1}".format(ENDIAN_NAME_TO_FORMAT[args["endian"]], format_char)


def pack_struct_float(value, format_char, **kwargs):
    return struct.pack(format_from_struct_float_arguments(format_char, kwargs), value)


def pack_float(value, **kwargs):
    byte_size = kwargs_int_byte_size(kwargs)
    if byte_size is None:
        byte_size = 4  # by default, we'll choose floats. If someone wants something different, he/she should define it.
    assert byte_size in STRUCT_FLOAT_PACKERS, "float must have a byte size of 4 or 8 but instead got {0}".format(byte_size)
    return STRUCT_FLOAT_PACKERS[byte_size](value, **kwargs)


STRUCT_FLOAT_PACKERS = {
    4: keep_kwargs_partial(pack_struct_float, format_char='f'),
    8: keep_kwargs_partial(pack_struct_float, format_char='q')
}


def unpack_struct_float(buffer, format_char, **kwargs):
    format = format_from_struct_float_arguments(format_char, kwargs)
    byte_size = struct.calcsize(format)
    assert len(buffer) >= byte_size, "buffer size must be at least {0} but instead got {1}".format(byte_size, len(buffer))
    return struct.unpack(format, str(buffer[0:byte_size]))[0], byte_size


def unpack_float(buffer, **kwargs):
    byte_size = kwargs_int_byte_size(kwargs)
    if byte_size is None:
        byte_size = 4  # by default, we'll choose floats. If someone wants something different, he/she should define it.
    assert byte_size in STRUCT_FLOAT_UNPACKERS, "float must have a byte size of 4 or 8 but instead got {0}".format(byte_size)
    return STRUCT_FLOAT_UNPACKERS[byte_size](buffer, **kwargs)

STRUCT_FLOAT_UNPACKERS = {
    4: keep_kwargs_partial(unpack_struct_float, format_char='f'),
    8: keep_kwargs_partial(unpack_struct_float, format_char='q')
}


#
# string support
#
JUSTIFY_OPTIONS = ('left', 'right', 'center')


def str_args_from_kwargs(kwargs):
    args = copy_defaults_and_override_with_kwargs(dict(encoding='ascii', padding=' ', justify='left'), kwargs)
    assert_kwarg_enum(args, 'justify', JUSTIFY_OPTIONS)
    assert len(args['padding']) == 1, "padding must be exactly one character but instead got {0!r}".format(args['padding'])
    return args


def pack_str(value, **kwargs):
    args = str_args_from_kwargs(kwargs)
    justify = args['justify']
    padding = args['padding']
    byte_size = kwargs_int_byte_size(args)
    result = bytearray(str(value).encode(args['encoding']))
    if byte_size is not None:
        if justify == 'left':
            result = result.ljust(byte_size, padding)
        elif justify == 'right':
            result = result.rjust(byte_size, padding)
        else:  # center
            result = result.center(byte_size, padding)
    return result


def unpack_str(buffer, **kwargs):
    args = str_args_from_kwargs(kwargs)
    justify = args['justify']
    padding = args['padding']
    strip = args['strip']
    byte_size = kwargs_int_byte_size(args)
    if byte_size and len(buffer) < byte_size:
        raise ValueError("str byte_size is {} but got buffer with len {}".format(byte_size, len(buffer)))

    value = str(buffer[0:byte_size]).decode(args['encoding'])
    if byte_size is not None:
        if justify == 'left':
            value = value.rstrip(strip).rstrip(padding)
        elif justify == 'right':
            value = value.lstrip(strip).lstrip(padding)
        else:  # center
            value = value.strip(strip).strip(padding)
    return value, len(buffer)


def pack_json(value, **kwargs):
    return pack_str(json.dumps(value), **kwargs)


def unpack_json(value, **kwargs):
    json_string, length = unpack_str(value, **kwargs)
    return json.loads(json_string.strip()), length


def pack_bytearray(buffer, **kwargs):
    return bytearray(buffer)


def unpack_bytearray(buffer, **kwargs):
    # Shortcuts before reverting to the generic conversion:
    if isinstance(buffer, bytearray):
        return buffer, len(buffer)
    elif isinstance(buffer, BitView):
        result = buffer.to_bytearray()
        return result, len(result)
    return bytearray(buffer), len(buffer)


#
# buffers support
#


def pack_buffer(value, **kwargs):
    return value.pack()


def unpack_buffer(buffer, **kwargs):
    obj = kwargs['type']()
    byte_size = obj.unpack(buffer)
    return obj, byte_size


def unpack_selector_decorator(selector):
    def my_selector(obj):
        o = selector(obj)
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


#
# lists support
#


def pack_list(list, elem_packer, **kwargs):
    result = BitAwareByteArray(bytearray())
    for o in list:
        result += elem_packer(o, **kwargs)
    return result


def unpack_list(buffer, elem_unpacker, **kwargs):
    n = kwargs.get('n', None)
    assert n is None or isinstance(n, (int, long)), "n must be either an integer or None but instead got {0!r}".format(n)
    byte_size = kwargs_fractional_byte_size(kwargs)

    result = []
    offset = 0
    index = 0
    while offset < buffer.length() and (n is None or index < n):
        unpacker_kwargs = copy_and_remove_kwargs(kwargs, ('buffer', 'n', 'index', 'container'))
        item, item_len = elem_unpacker(buffer[offset:byte_size], index=index, n=n, container=result, **unpacker_kwargs)
        result.append(item)
        offset += item_len
        index += 1
    return result, offset
