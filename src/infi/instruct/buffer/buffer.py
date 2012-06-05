import sys
import traceback
import itertools
from itertools import chain

from ..utils import format_exception
from .range import SequentialRange
from .reference import Context, Reference, NumericReference
from .reference import FuncCallReference, NumericFuncCallReference
from .reference import GetAttrReference, NumericGetAttrReference, ContextGetAttrReference
from .reference import SetAttrReference, SetAndGetAttrReference, NumericSetAndGetAttrReference, ObjectReference
from .io_buffer import InputBuffer, OutputBuffer

class InstructBufferError(Exception):
    MESSAGE = """{error_msg} - attribute '{attr_name}' in class '{clazz}':
  Instruct internal call stack:
{context_call_stack}

  Inner exception:
{formatted_exception}"""
    def __init__(self, error_msg, ctx, clazz, attr_name, exc_info):
        # Format the inner exception to look like a normal Python exeception output, but indented with 2 spaces.
        inner_exception = format_exception(exc_info, "    ")

        # Format the context call stack, so it will be clearer.
        context_call_stack = "\n".join([ "    {0}".format(line) for line in ctx.format_exception_call_stack() ])

        self.clazz = clazz
        self.attr_name = attr_name
        self.exc_info = exc_info
        self.msg = type(self).MESSAGE.format(error_msg=error_msg, attr_name=attr_name, clazz=clazz,
                                             context_call_stack=context_call_stack,
                                             formatted_exception=inner_exception)

    def __str__(self):
        return self.msg

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
            # Object has dynamic size, so we'll get it from the absolute position of each field.
            positions = itertools.chain(*[ field.absolute_position_ref(ctx) for field in ctx.fields ])
            result = SequentialRange.list_max_stop(positions) # total_size calculation
            assert result is not None
            return result
        else:
            return ctx.input_buffer.length()

    def __safe_repr__(self):
        return "total_size"

class AbsolutePositionReference(Reference):
    def __init__(self, field, pack_position_ref, unpack_position_ref):
        self.field = field
        self.pack_position_ref = pack_position_ref
        self.unpack_position_ref = unpack_position_ref

    def evaluate(self, ctx):
        if ctx.is_pack():
            return self.eval_pack(ctx)
        else:
            return self.eval_unpack(ctx)

    def eval_pack(self, ctx):
        position_list = self.pack_position_ref(ctx)
        if SequentialRange.list_overlaps(position_list):
            raise ValueError("field position list has overlapping ranges")

        if any([ pos.is_open() for pos in position_list ]):
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

    def eval_unpack(self, ctx):
        position_list = self.unpack_position_ref(ctx)
        if SequentialRange.list_overlaps(position_list):
            raise ValueError("field position list has overlapping ranges")

        buffer_len = ctx.input_buffer.length()
        return [ pos.to_closed(buffer_len) for pos in position_list ]

    def __safe_repr__(self):
        return "abs_position({0!r})".format(self.field)

class FieldReference(Reference):
    attr_name_ref = None
    pack_value_ref = None
    unpack_value_ref = None
    pack_ref = None
    unpack_ref = None
    absolute_position_ref = None

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

class FieldReferenceBuilder(object):
    def __init__(self):
        self.pack_value = None
        self.unpack_value = None
        self.pack_position = None
        self.unpack_position = None
        self.position = None
        self.numeric = False
        self.pack_class = None
        self.pack_class_requires_position = False
        self.unpack_class = None

    def set_pack_value(self, pack_value):
        self.pack_value = pack_value
        return self

    def set_unpack_value(self, unpack_value):
        self.unpack_value = unpack_value
        return self

    def set_pack_position(self, pack_position):
        self.pack_position = pack_position
        return self

    def set_unpack_position(self, unpack_position):
        self.unpack_position = unpack_position
        return self

    def set_position(self, position):
        self.position = position
        return self

    def set_numeric(self, numeric):
        self.numeric = numeric
        return self

    def set_unpack_class(self, unpack_class):
        self.unpack_class = unpack_class
        return self

    def set_pack_class(self, pack_class, requires_position=False):
        self.pack_class = pack_class
        self.pack_class_requires_position = requires_position
        return self

    def create(self):
        field_class = NumericFieldReference if self.numeric else FieldReference
        field = field_class()

        get_obj_from_ctx_ref = ContextGetAttrReference('obj')

        # When we first create a field reference we don't know the field name yet. When __new__ will get called
        # on Buffer, it will fill it in for us.
        field.attr_name_ref = ObjectReference(None)

        self._set_position_on_field(field)

        set_and_get_class = NumericSetAndGetAttrReference if self.numeric else SetAndGetAttrReference

        if self.pack_value is not None:
            if not isinstance(self.pack_value, Reference):
                pack_value_class = NumericFuncCallReference if self.numeric else FuncCallReference
                pack_value_ref = pack_value_class(self.pack_value, get_obj_from_ctx_ref)
            else:
                pack_value_ref = self.pack_value
            field.pack_value_ref = set_and_get_class(get_obj_from_ctx_ref, field.attr_name_ref, pack_value_ref)
        else:
            getter_ref_class = NumericGetAttrReference if self.numeric else GetAttrReference
            field.pack_value_ref = getter_ref_class(get_obj_from_ctx_ref, field.attr_name_ref)

        if self.pack_class_requires_position:
            field.pack_ref = self.pack_class(field.pack_value_ref, field.absolute_position_ref)
        else:
            field.pack_ref = self.pack_class(field.pack_value_ref)

        field.unpack_ref = self.unpack_class(field.absolute_position_ref)
        field.unpack_value_ref = set_and_get_class(get_obj_from_ctx_ref, field.attr_name_ref, field.unpack_ref)

        return field

    def _set_position_on_field(self, field):
        if self.pack_position is not None:
            assert self.unpack_position is not None and self.position is None
            pack_position_ref = self.pack_position
            unpack_position_ref = self.unpack_position
        else:
            assert self.unpack_position is None and self.position is not None
            pack_position_ref = self.position
            unpack_position_ref = self.position

        field.absolute_position_ref = AbsolutePositionReference(field, pack_position_ref, unpack_position_ref)

class BufferType(type):
    def __new__(cls, name, bases, attrs):
        # If we initialize our own class don't do any modifications.
        if name == "Buffer":
            return super(BufferType, cls).__new__(cls, name, bases, attrs)

        # FIXME: add support for __init__ that extracts values from kwargs
        # We want to first put our own __init__ method that will initialize all the fields passed by kwargs and then
        # call the user's __init__ method (if exists) with args/kwargs left.
        # if "__init__" in attrs:
        #    user_init = attrs["__init__"]
        #    del attrs["__init__"]
        #else:
        #    user_init = None

        new_cls = super(BufferType, cls).__new__(cls, name, bases, attrs)

        # First off, assign names and getters/setters to all the field references and find all the fields.
        fields = []
        for attr_name in dir(new_cls):
            attr = getattr(new_cls, attr_name)
            if isinstance(attr, FieldReference) and not attr.is_initialized():
                attr.init(attr_name)
                fields.append(attr)

        setattr(new_cls, 'byte_size', cls.calc_byte_size(name, fields))
        setattr(new_cls, '__fields__', fields)
        return new_cls

    @classmethod
    def calc_byte_size(cls, class_name, fields):
        # We want to see if this class has static size, i.e. all the field positions can be resolved without looking
        # up attributes on the object.
        # The simplest way to do that is to try to resolve all the positions, and if any position requires an object
        # lookup we raise an exception.
        class DynamicSizeObjectError(Exception):
            pass

        class FakeObject(object):
            def __getattr__(self, name):
                raise DynamicSizeObjectError()

        ctx = PackContext(FakeObject(), fields)
        positions = []
        for field in fields: # we avoid list comprehension here so we'll know which field raised an error
            try:
                positions.extend(field.absolute_position_ref(ctx))
            except DynamicSizeObjectError:
                return None
            except:
                raise InstructBufferError("Error while calculating static byte size", ctx, class_name,
                                          field.attr_name(), sys.exc_info())
        return SequentialRange.list_max_stop(positions)

class Buffer(object):
    __metaclass__ = BufferType

    def __init__(self, *args, **kwargs):
        super(Buffer, self).__init__(*args, **kwargs)

    def pack(self):
        """Packs the object and returns a buffer representing the packed object."""
        fields = type(self).__fields__
        ctx = PackContext(self, fields)

        for field in fields:
            try:
                ctx.output_buffer.set(field.pack_ref(ctx), field.absolute_position_ref(ctx))
            except:
                raise InstructBufferError("Pack error occured", ctx, type(self), field.attr_name(), sys.exc_info())

        return ctx.output_buffer.get()

    def unpack(self, buffer):
        """Unpacks the object's fields from buffer."""
        fields = type(self).__fields__
        ctx = UnpackContext(self, fields, buffer)

        for field in fields:
            try:
                field.unpack_value_ref(ctx)
            except:
                raise InstructBufferError("Unpack error occurred", ctx, type(self), field.attr_name(),
                                          sys.exc_info())

        return self.calc_byte_size()

    def calc_byte_size(self):
        """
        Returns this instance's size. If the size has to be calculated it may require packing some of the fields.
        """
        return TotalSizeReference()(PackContext(self, type(self).__fields__))

    def __repr__(self):
        fields = type(self).__fields__
        repr_fields = [ "{0}={1!r}".format(field.attr_name(), getattr(self, field.attr_name())) for field in fields ]
        return "{0}.{1}({2})".format(type(self).__module__, type(self).__name__, ", ".join(repr_fields))
