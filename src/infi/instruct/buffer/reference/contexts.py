from infi.instruct.buffer.io_buffer import InputBuffer, OutputBuffer

from .reference import Reference, Context
from .builtins import GetAttrReference


class BufferContext(Context):
    """Base class for buffer context. Contains the object we're packing/unpacking and the list of fields."""

    def __init__(self, obj, fields):
        super(BufferContext, self).__init__()
        self.obj = obj
        self.fields = fields

    def is_pack(self):
        return isinstance(self, PackContext)

    def is_unpack(self):
        return isinstance(self, UnpackContext)

    def has_field(self, name):
        return any(field.attr_name() == name for field in self.fields)

    def get_field(self, name):
        return next(field for field in self.fields if field.attr_name() == name)


class PackContext(BufferContext):
    """Context used when packing. Contains the object, fields and output buffer."""

    def __init__(self, obj, fields, output_buffer=None):
        super(PackContext, self).__init__(obj, fields)
        self.output_buffer = OutputBuffer() if not output_buffer else output_buffer


class UnpackContext(BufferContext):
    """Context used when unpacking. Contains the object, fields and input buffer."""

    def __init__(self, obj, fields, input_buffer):
        super(UnpackContext, self).__init__(obj, fields)
        self.input_buffer = InputBuffer(input_buffer)


class ReturnContextReference(Reference):
    """A reference that evaluates to the context itself (useful when using FuncCallReference)."""
    def __init__(self):
        super(ReturnContextReference, self).__init__(False)

    def evaluate(self, ctx):
        return ctx

    def __safe_repr__(self):
        return "ctx"


class ContextGetAttrReference(GetAttrReference):
    """A reference that returns an attribute from the context."""

    def __init__(self, numeric, attr_name):
        super(ContextGetAttrReference, self).__init__(numeric, ReturnContextReference(), attr_name)


class InputBufferLengthReference(Reference):
    def __init__(self):
        super(InputBufferLengthReference, self).__init__(True)

    def evaluate(self, ctx):
        return ctx.input_buffer.length()

    def __safe_repr__(self):
        return "len(input_buffer)"
