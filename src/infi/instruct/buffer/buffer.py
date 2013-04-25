import math
import itertools

from infi import exceptools
from ..errors import InstructError

from .range import SequentialRangeList
from .reference import Context, Reference, NumericReference
from .io_buffer import InputBuffer, OutputBuffer


class InstructBufferError(InstructError):
    MESSAGE = """{error_msg} - attribute '{attr_name}' in class '{clazz}':
  Instruct internal call stack:
{context_call_stack}"""

    def __init__(self, error_msg, ctx, clazz, attr_name):
        # Format the context call stack, so it will be clearer.
        context_call_stack = "\n".join(["    {0}".format(line) for line in ctx.format_exception_call_stack()])
        msg = type(self).MESSAGE.format(error_msg=error_msg, attr_name=attr_name, clazz=clazz,
                                        context_call_stack=context_call_stack)
        super(InstructBufferError, self).__init__(msg)

        self.clazz = clazz
        self.attr_name = attr_name


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


class PackContext(BufferContext):
    """Context used when packing. Contains the object, fields and output buffer."""

    def __init__(self, obj, fields):
        super(PackContext, self).__init__(obj, fields)
        self.output_buffer = OutputBuffer()


class UnpackContext(BufferContext):
    """Context used when unpacking. Contains the object, fields and input buffer."""

    def __init__(self, obj, fields, input_buffer):
        super(UnpackContext, self).__init__(obj, fields)
        self.input_buffer = InputBuffer(input_buffer)


class TotalSizeReference(Reference, NumericReference):
    def evaluate(self, ctx):
        # First, we'll try a shortcut - if the size is static, we'll return that since we precalculated it.
        size = getattr(type(ctx.obj), 'byte_size', None)
        if size is not None:
            return size

        if ctx.is_pack():
            lists = [field.pack_absolute_position_ref(ctx) for field in ctx.fields]
            positions = SequentialRangeList(itertools.chain(*lists))
            result = positions.max_stop()  # total_size calculation
        else:
            result = max(self._unpack_position_list_for_field(ctx, field) for field in ctx.fields)

        assert result is not None
        return result

    def _unpack_position_list_for_field(self, ctx, field):
        result = field.unpack_absolute_position_ref.unpack_position_ref(ctx).byte_offset(field.unpack_ref(ctx)[1])
        return result

    def __safe_repr__(self):
        return "total_size"


class PackAbsolutePositionReference(Reference):
    def __init__(self, field, pack_position_ref):
        self.field = field
        self.pack_position_ref = pack_position_ref

    def is_open(self, ctx):
        return self.pack_position_ref(ctx).is_open()

    def evaluate(self, ctx):
        position_list = self.pack_position_ref(ctx)
        if position_list.has_overlaps():
            raise ValueError("field position list has overlapping ranges")

        if position_list.is_open():
            # We need the serialization result of this field to set the range. Note that we already checked if the
            # position has overlapping ranges, so there may be only a single open range.
            packed_field = self.field.pack_ref(ctx)
            current_length = 0
            absolute_position_list = []
            for pos in position_list:
                abs_pos = pos.to_closed(pos.start + len(packed_field) - current_length)
                absolute_position_list.append(abs_pos)
                current_length += abs_pos.length()
            return absolute_position_list
        else:
            return position_list

    def __safe_repr__(self):
        return "pack_abs_position({0!r}, {1!r})".format(self.field, self.position_list)


class UnpackAbsolutePositionReference(Reference):
    def __init__(self, field, unpack_position_ref):
        self.field = field
        self.unpack_position_ref = unpack_position_ref

    def is_open(self, ctx):
        return self.unpack_position_ref(ctx).is_open()

    def evaluate(self, ctx):
        position_list = self.unpack_position_ref(ctx)
        if position_list.has_overlaps():
            raise ValueError("field position list has overlapping ranges")

        if position_list.is_open():
            buffer_len = ctx.input_buffer.length()
            return position_list.to_closed(buffer_len)

        return position_list

    def __safe_repr__(self):
        return "unpack_abs_position(field={0!r}, {1!r})".format(self.field, self.unpack_position_ref)


class FieldReference(Reference):
    attr_name_ref = None
    pack_value_ref = None
    unpack_value_ref = None
    pack_ref = None
    unpack_ref = None
    pack_absolute_position_ref = None
    unpack_absolute_position_ref = None
    unpack_after = None
    default = None

    def init(self, name):
        self.attr_name_ref.obj = name

    def is_initialized(self):
        return self.attr_name_ref.obj is not None

    def attr_name(self):
        return self.attr_name_ref.obj

    def evaluate(self, ctx):
        if ctx.is_pack():
            return self.pack_value_ref(ctx)
        else:
            return self.unpack_value_ref(ctx)

    def __safe_repr__(self):
        return "field_ref({0!r})".format(self.attr_name_ref.obj)


class NumericFieldReference(FieldReference, NumericReference):
    def __safe_repr__(self):
        return "num_field_ref({0!r})".format(self.attr_name_ref.obj)


class BufferType(type):
    def __new__(cls, name, bases, attrs):
        # If we initialize our own class don't do any modifications.
        if name == "Buffer":
            return super(BufferType, cls).__new__(cls, name, bases, attrs)

        new_cls = super(BufferType, cls).__new__(cls, name, bases, attrs)

        # First off, assign names and getters/setters to all the field references and find all the fields.
        fields = []
        for attr_name in dir(new_cls):
            attr = getattr(new_cls, attr_name)
            if isinstance(attr, FieldReference) and not attr.is_initialized():
                attr.init(attr_name)
                fields.append(attr)

        setattr(new_cls, 'byte_size', attrs['byte_size'] if 'byte_size' in attrs else cls.calc_byte_size(name, fields))
        setattr(new_cls, '__fields__', fields)
        return new_cls

    @classmethod
    def calc_byte_size(cls, class_name, fields):
        ctx = PackContext(None, fields)
        positions = SequentialRangeList()
        for field in fields:  # we avoid list comprehension here so we'll know which field raised an error
            try:
                if not (field.pack_absolute_position_ref.is_static()
                        and field.unpack_absolute_position_ref.is_static()):
                    return None
                positions.extend(field.pack_absolute_position_ref(ctx))
            except:
                raise exceptools.chain(InstructBufferError("Error while calculating static byte size", ctx,
                                                           class_name, field.attr_name()))
        return positions.max_stop()


class Buffer(object):
    __metaclass__ = BufferType

    def __init__(self, **kwargs):
        super(Buffer, self).__init__()

        field_names = self._all_field_names()
        for name, value in kwargs.items():
            assert name in field_names, ("field {0} in class {1} is not defined but passed to Buffer's __init__"
                                         .format(name, type(self)))
            setattr(self, name, value)

        for field in self._all_fields():
            if isinstance(getattr(self, field.attr_name()), FieldReference):
                setattr(self, field.attr_name(), field.default)

    def pack(self):
        """Packs the object and returns a buffer representing the packed object."""
        fields = self._all_fields()
        ctx = PackContext(self, fields)

        for field in fields:
            try:
                ctx.output_buffer.set(field.pack_ref(ctx), field.pack_absolute_position_ref(ctx))
            except:
                raise exceptools.chain(InstructBufferError("Pack error occured", ctx, type(self), field.attr_name()))

        result = bytearray(ctx.output_buffer.get())

        # We want to support the user defining the buffer's fixed byte size but not using it all:
        static_byte_size = type(self).byte_size
        if static_byte_size:
            static_byte_size = int(math.ceil(static_byte_size))
            assert len(result) <= static_byte_size, \
                ("in type {0} computed pack size is {1} but declared byte size is {2} - perhaps you manually defined " +
                 "the byte size in the type but the actual size is bigger?").format(type(self), len(result),
                                                                                    static_byte_size)
            if len(result) < static_byte_size:
                result += bytearray(static_byte_size - len(result))
        return result

    def unpack(self, buffer):
        """Unpacks the object's fields from buffer."""
        fields = self._all_fields()
        ctx = UnpackContext(self, fields, buffer)

        for field in fields:
            try:
                for prev_field in field.unpack_after:
                    prev_field.unpack_value_ref(ctx)
                field.unpack_value_ref(ctx)
            except:
                raise exceptools.chain(InstructBufferError("Unpack error occurred", ctx, type(self), field.attr_name()))

        return self.calc_byte_size(ctx)

    def calc_byte_size(self, ctx=None):
        """
        Returns this instance's size. If the size has to be calculated it may require packing some of the fields.
        """
        if ctx is None:
            ctx = PackContext(self, type(self).__fields__)
        return TotalSizeReference()(ctx)

    def _all_fields(self):
        fields = []
        for cls in type(self).mro():
            cls_fields = getattr(cls, '__fields__', [])
            fields.extend(cls_fields)
        return fields

    def _all_field_names(self):
        return set(field.attr_name() for field in self._all_fields())

    def __repr__(self):
        fields = type(self).__fields__
        repr_fields = ["{0}={1!r}".format(field.attr_name(), getattr(self, field.attr_name())) for field in fields]
        return "{0}.{1}({2})".format(type(self).__module__, type(self).__name__, ", ".join(repr_fields))
