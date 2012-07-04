import sys
import struct
import functools
from infi import exceptools

from .reference import Reference, NumericReference, Context
from .buffer import PackContext, UnpackContext
from .io_buffer import InputBuffer, BitAwareByteArray
from .range import SequentialRange

from ..utils import format_exception
from ..errors import InstructError

class PackError(InstructError):
    MESSAGE = "{pack_ref!r} failed to pack {value!r}."
    def __init__(self, pack_ref, value):
        super(PackError, self).__init__(PackError.MESSAGE.format(pack_ref=pack_ref, value=value))

class UnpackError(InstructError):
    MESSAGE = "{unpack_ref!r} failed to pack {buffer!r}."
    def __init__(self, unpack_ref, buffer):
        super(UnpackError, self).__init__(UnpackError.MESSAGE.format(unpack_ref=unpack_ref, buffer=buffer))

class Packer(object):
    byte_size = None

    def pack(self, object):
        raise NotImplementedError()

class FillPacker(object):
    byte_size = None

    def pack(self, object, byte_size):
        raise NotImplementedError()

class Unpacker(object):
    byte_size = None

    def unpack(self, ctx, buffer):
        raise NotImplementedError()

ENDIAN_NAME_TO_FORMAT = { 'unspecified': '@', 'native': '=', 'big': '>', 'little': '<' }
SIGN_NAMES = ("signed", "unsigned")

class NumberMarshal(Packer, Unpacker):
    struct_format = None

    def __init__(self, sign_name="signed", endian_name="unspecified"):
        self.sign_name = sign_name
        self.endian_name = endian_name

        struct_format_char = self.struct_format.lower() if sign_name == "signed" else self.struct_format.upper()
        self.format = "{0}{1}".format(ENDIAN_NAME_TO_FORMAT[endian_name], struct_format_char)

    def pack(self, value):
        return struct.pack(self.format, value)

    def unpack(self, ctx, buffer):
        assert len(buffer) == self.byte_size, "buffer size must be {0} but instead got {1}".format(self.byte_size,
                                                                                                   len(buffer))
        return struct.unpack(self.format, str(buffer))[0], self.byte_size

    def __repr__(self):
        return "{0}_int{1}_{2}_endian".format(self.sign_name, self.byte_size * 8, self.endian_name)

class BitIntMarshal(Packer, Unpacker):
    def __init__(self, byte_size):
        self.byte_size = byte_size

    def pack(self, value):
        result = BitAwareByteArray(bytearray(1), 0, self.byte_size)
        result[0:] = value
        return result

    def unpack(self, ctx, buffer):
        return buffer[0:self.byte_size][0], self.byte_size

class Int8Marshal(NumberMarshal):
    byte_size = 1
    struct_format = "b"

class Int16Marshal(NumberMarshal):
    byte_size = 2
    struct_format = "h"

class Int32Marshal(NumberMarshal):
    byte_size = 4
    struct_format = "l"

class Int64Marshal(NumberMarshal):
    byte_size = 8
    struct_format = "q"

class Float32Marshal(NumberMarshal):
    byte_size = 4
    struct_format = "f"

    def __init__(self, endian_name="unspecified"):
        super(Float32Marshal, self).__init__("signed", endian_name)

    def __repr__(self):
        return "float32_{0}_endian".format(self.endian_name)

class Float64Marshal(NumberMarshal):
    byte_size = 8
    struct_format = "d"

    def __init__(self, endian_name="unspecified"):
        super(Float64Marshal, self).__init__("signed", endian_name)

    def __repr__(self):
        return "float64_{0}_endian".format(self.endian_name)

INT_MARSHALS = { 1: Int8Marshal, 2: Int16Marshal, 4: Int32Marshal, 8: Int64Marshal }
class IntMarshal(FillPacker, Unpacker):
    def __init__(self, sign_name="unsigned", endian_name="unspecified"):
        assert sign_name in SIGN_NAMES
        assert endian_name in ENDIAN_NAME_TO_FORMAT.keys()
        self.sign_name = sign_name
        self.endian_name = endian_name

    def pack(self, value, byte_size):
        if byte_size < 1:
            marshal = BitIntMarshal(byte_size)
        else:
            marshal = type(self).create_size_specific_marshal(self.sign_name, self.endian_name, byte_size)
        return marshal.pack(value)

    def unpack(self, ctx, buffer):
        if byte_size < 1:
            marshal = BitIntMarshal(buffer.length())
        else:
            marshal = type(self).create_size_specific_marshal(self.sign_name, self.endian_name, buffer.length())
        return marshal.unpack(ctx, buffer)

    def __repr__(self):
        return "{0}_int_{1}_endian".format(self.sign_name, self.endian_name)

    @classmethod
    def create_size_specific_marshal(cls, sign_name, endian_name, byte_size):
        return INT_MARSHALS[byte_size](sign_name, endian_name)

FLOAT_MARSHALS = { 4: Float32Marshal, 8: Float64Marshal }
class FloatMarshal(IntMarshal):
    def __init__(self, endian_name="unspecified"):
        super(FloatMarshal, self).__init__("signed", endian_name)

    def __repr__(self):
        return "float_{1}_endian".format(self.endian_name)

    @classmethod
    def create_size_specific_marshal(cls, sign_name, endian_name, byte_size):
        assert sign_name == "signed"
        return FLOAT_MARSHALS[byte_size](endian_name)

class ListPacker(Packer):
    def __init__(self, item_packer, n_items=None):
        self.item_packer = item_packer
        self.n_items = n_items
        if item_packer.byte_size is not None and n_items is not None:
            self.byte_size = item_packer.byte_size * n_items

    def pack(self, list):
        assert self.n_items is None or (len(list) == self.n_items)

        result = BitAwareByteArray(bytearray())
        for item in list:
            result += self.item_packer.pack(item)

        assert self.byte_size is None or (self.byte_size == result.length())
        return result

    def __repr__(self):
        return "{0!r}_list{1}".format(self.item_packer, "[%d]" % (self.n_items,) if self.n_items is not None else "")

class ListUnpacker(Unpacker):
    def __init__(self, item_unpacker, n_items=None):
        self.item_unpacker = item_unpacker
        self.n_items = n_items
        if item_unpacker.byte_size is not None and n_items is not None:
            self.byte_size = item_unpacker.byte_size * n_items

    def unpack(self, ctx, buffer):
        result = []
        n_items = self.n_items
        item_len = self.item_unpacker.byte_size
        if n_items is None and item_len is not None:
            # We can determine how many elements in the list since we know each element's size.
            n_items = buffer.length() / item_len

        result = []
        offset = 0
        if item_len is not None:
            for i in xrange(n_items):
                item, _ = self.item_unpacker.unpack(ctx, buffer[offset:offset + item_len])
                result.append(item)
                offset += item_len
        else:
            while offset < buffer.length():
                item, item_len = self.item_unpacker.unpack(ctx, buffer[offset:])
                result.append(item)
                offset += item_len
            assert offset == buffer.length()

        return result, offset

    def __repr__(self):
        return "{0!r}_list{1}".format(self.item_packer, "[%d]" % (self.n_items,) if self.n_items is not None else "")

class StringMarshal(Packer, Unpacker):
    def __init__(self, encoding='ascii'):
        self.encoding = encoding

    def pack(self, value):
        return bytearray(str(value).encode(self.encoding))

    def unpack(self, ctx, buffer):
        result = str(buffer).decode(self.encoding)
        return result, len(result)

JUSTIFY_OPTIONS = ('left', 'right', 'center')
class FillStringMarshal(FillPacker, Unpacker):
    def __init__(self, justify='left', padding='\x00', encoding='ascii'):
        self.justify = justify
        self.padding = padding
        self.encoding = encoding

    def pack(self, value, byte_size):
        result = str(value).encode(self.encoding)
        if self.justify == 'left':
            result = result.ljust(byte_size, self.padding)
        elif self.justify == 'right':
            result = result.rjust(byte_size, self.padding)
        else: # center
            result = result.center(byte_size, self.padding)
        return bytearray(result)

    def unpack(self, ctx, buffer):
        value = str(buffer).decode(self.encoding)
        if self.justify == 'left':
            value = value.rstrip(self.padding)
        elif self.justify == 'right':
            value = value.lstrip(self.padding)
        else: # center
            value = value.strip(self.padding)
        return value, len(value)

class BufferMarshal(Packer, Unpacker):
    def __init__(self, buffer_cls):
        self.buffer_cls = buffer_cls
        self.byte_size = self.buffer_cls.byte_size

    def pack(self, value):
        return value.pack()

    def unpack(self, ctx, buffer):
        item = self.buffer_cls()
        size = item.unpack(buffer)
        return item, size

class PackerReference(Reference):
    byte_size = None

    def __init__(self, packer, value_ref):
        assert value_ref is not None
        self.packer = packer
        self.value_ref = value_ref
        self.byte_size = self.packer.byte_size

    def evaluate(self, ctx):
        value = self.value_ref(ctx)
        try:
            return self.packer.pack(value)
        except:
            raise exceptools.chain(PackError(self, value))

    def __safe_repr__(self):
        return "{0!r}_pack({1!r})".format(self.packer, self.value_ref)

class FillPackerReference(Reference):
    byte_size = None

    def __init__(self, packer, byte_size_ref, value_ref):
        assert value_ref is not None
        self.packer = packer
        self.byte_size_ref = byte_size_ref
        self.value_ref = value_ref

    def evaluate(self, ctx):
        value = self.value_ref(ctx)
        byte_size = self.byte_size_ref(ctx)
        try:
            return self.packer.pack(value, byte_size)
        except:
            raise exceptools.chain(PackError(self, value))

    def __safe_repr__(self):
        return "{0!r}_pack({1!r}, {2!r})".format(self.packer, self.value_ref, self.byte_size_ref)

class UnpackerReference(Reference):
    byte_size = None

    def __init__(self, unpacker, absolute_position_ref):
        self.unpacker = unpacker
        self.absolute_position_ref = absolute_position_ref
        self.byte_size = self.unpacker.byte_size

    def get_absolute_position(self, ctx):
        return self.absolute_position_ref(ctx)

    def evaluate(self, ctx):
        buffer = ctx.input_buffer.get(self.absolute_position_ref(ctx))
        try:
            value, byte_size = self.unpacker.unpack(ctx, buffer)
            return value
        except:
            raise exceptools.chain(UnpackError(self, buffer))

    def __safe_repr__(self):
        return "{0!r}_unpack({1!r})".format(self.unpacker, self.absolute_position_ref)
