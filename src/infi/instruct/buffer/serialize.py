import sys
import struct
import functools
from .reference import Reference, NumericReference, Context
from .buffer import PackContext, UnpackContext
from .io_buffer import InputBuffer
from .range import SequentialRange
from ..utils import format_exception

# FIXME: better base exception here
class PackError(Exception):
    MESSAGE = "{pack_ref!r} failed to pack {value!r}.\n  Inner exception:\n{inner_exception}"

    def __init__(self, pack_ref, value, exc_info):
        super(PackError, self).__init__(PackError.MESSAGE.format(pack_ref=pack_ref, value=value,
                                                                 inner_exception=format_exception(exc_info, "    ")))

# FIXME: better base exception here
class UnpackError(Exception):
    MESSAGE = "{unpack_ref!r} failed to pack {buffer!r}.\n  Inner exception:\n{inner_exception}"
    def __init__(self, unpack_ref, buffer, exc_info):
        super(UnpackError, self).__init__(UnpackError.MESSAGE.format(unpack_ref=unpack_ref, buffer=buffer,
                                                                     inner_exception=format_exception(exc_info,
                                                                                                      "    ")))

class PackReference(Reference):
    def __init__(self, value_ref):
        assert value_ref is not None
        self.value_ref = value_ref

    def evaluate(self, ctx):
        value = self.value_ref(ctx)
        try:
            return self.pack(value)
        except:
            raise PackError(self, value, sys.exc_info())

    def pack(self, value):
        raise NotImplementedError()

class UnpackReference(Reference):
    def __init__(self, absolute_position_ref):
        self.absolute_position_ref = absolute_position_ref

    def get_absolute_position(self, ctx):
        return self.absolute_position_ref(ctx)

    def get_input(self, ctx):
        return ctx.input_buffer.get(self.get_absolute_position(ctx))

    def evaluate(self, ctx):
        buffer = self.get_input(ctx)
        try:
            return self.unpack(buffer)
        except:
            raise UnpackError(self, buffer, sys.exc_info())

    def unpack(self, buffer):
        raise NotImplementedError()

class StringPackReference(PackReference):
    def pack(self, value):
        return bytearray(value)

class StringUnpackReference(UnpackReference):
    def unpack(self, buffer):
        return str(buffer)

class UBInt32PackReference(PackReference):
    byte_size = 4

    def pack(self, value):
        return struct.pack(">L", value)

    def __safe_repr__(self):
        return "ub_int32_pack({0!r})".format(self.value_ref)

class UBInt32UnpackReference(UnpackReference, NumericReference):
    byte_size = 4

    def unpack(self, buffer):
        assert len(buffer) == 4, "buffer size must be 4 but instead got {0}".format(len(buffer))
        return struct.unpack(">L", str(buffer))[0]

    def __safe_repr__(self):
        return "ub_int32_unpack({0!r})".format(self.absolute_position_ref)

class BufferPackReference(PackReference):
    def __init__(self, buffer_cls, value_ref):
        super(BufferPackReference, self).__init__(value_ref)
        self.buffer_cls = buffer_cls

    def pack(self, value):
        return value.pack()

    def __safe_repr__(self):
        return "{0}.pack({1!r})".format(repr(self.buffer_cls), self.value_ref)

    @classmethod
    def create_factory(cls, buffer_cls):
        return functools.partial(BufferPackReference, buffer_cls)

class BufferUnpackReference(UnpackReference):
    def __init__(self, buffer_cls, value_ref):
        super(BufferUnpackReference, self).__init__(value_ref)
        self.buffer_cls = buffer_cls

    def unpack(self, buffer):
        obj = self.buffer_cls()
        obj.unpack(buffer)
        return obj

    def __safe_repr__(self):
        return "{0}.unpack({1!r})".format(repr(self.buffer_cls), self.absolute_position_ref)

    @classmethod
    def create_factory(cls, buffer_cls):
        return functools.partial(BufferUnpackReference, buffer_cls)

class ListPackContext(Context):
    def __init__(self, list, n):
        super(ListPackContext, self).__init__()
        self.list = list
        self.n = n

class ListElementReference(Reference):
    def evaluate(self, ctx):
        return ctx.list[ctx.n]

    def __safe_repr__(self):
        "array_element_ref"

class ListPackReference(PackReference):
    def __init__(self, element_pack_cls, value_ref):
        super(ListPackReference, self).__init__(value_ref)
        self.list_element_ref = ListElementReference()
        self.element_pack = element_pack_cls(self.list_element_ref)

    def pack(self, list):
        result = bytearray()
        for n in xrange(len(list)):
            ctx = ListPackContext(list, n)
            result += self.element_pack(ctx)
        return result

    def __safe_repr__(self):
        return "list_pack({0!r})".format(self.element_pack_cls)

    @classmethod
    def create_factory(cls, element_pack_cls):
        return functools.partial(ListPackReference, element_pack_cls)

class ListUnpackContext(Context):
    def __init__(self, buffer, bytes_read):
        super(ListUnpackContext, self).__init__()
        self.input_buffer = InputBuffer(buffer)
        self.bytes_read = bytes_read

class FixedSizeElementPositionReference(Reference, NumericReference):
    def __init__(self, size):
        self.size = size

    def evaluate(self, ctx):
        return [ SequentialRange(ctx.bytes_read, ctx.bytes_read + self.size) ]

class FixedSizeListUnpackReference(UnpackReference):
    def __init__(self, element_unpack_cls, element_size, absolute_position_ref):
        super(FixedSizeListUnpackReference, self).__init__(absolute_position_ref)
        self.element_size = element_size
        self.element_position_ref = FixedSizeElementPositionReference(element_size)
        self.element_unpack = element_unpack_cls(self.element_position_ref)

    def unpack(self, buffer):
        result = []
        bytes_read = 0
        while bytes_read < len(buffer):
            ctx = ListUnpackContext(buffer, bytes_read)
            result.append(self.element_unpack(ctx))
            bytes_read += self.element_size

        return result

    def __safe_repr__(self):
        return "fixed_size_list_unpack({0!r}, {1!r}, {2!r})".format(self.element_unpack,
                                                                    self.element_size,
                                                                    self.absolute_position_ref)

    @classmethod
    def create_factory(cls, element_unpack_cls, element_size):
        return functools.partial(FixedSizeListUnpackReference, element_unpack_cls, element_size)
