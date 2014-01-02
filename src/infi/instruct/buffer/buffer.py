import math
import itertools

from infi import exceptools
from infi.instruct.utils.safe_repr import safe_repr
from infi.instruct.errors import InstructError

from .range import SequentialRangeList
from .reference import Reference, FieldReference, PackContext, UnpackContext, TotalSizeReference
from .io_buffer import InputBuffer, OutputBuffer


class InstructBufferError(InstructError):
    MESSAGE = """{error_msg} - attribute '{attr_name}' in class '{clazz}':
  Resolved References:
{resolved_references}

  Instruct internal call stack:
{context_call_stack}"""

    def __init__(self, error_msg, ctx, clazz, attr_name):
        # Format the context call stack, so it will be clearer.
        context_call_stack = "\n".join(["    {0}".format(line) for line in ctx.format_exception_call_stack()])

        # Format a list of all resolved references, remove identity ones (e.g. 1=1, etc.) and show only uniques
        resolved_reference_pairs = [(safe_repr(key), repr(value)) for key, value in ctx.cached_results.iteritems()]
        resolved_reference_str_list = sorted(["    {0}={1}".format(a, b) for a, b in resolved_reference_pairs
                                              if a != b])
        resolved_references = "\n".join(s for s, _ in itertools.groupby(resolved_reference_str_list))
        msg = type(self).MESSAGE.format(error_msg=error_msg, attr_name=attr_name, clazz=clazz,
                                        context_call_stack=context_call_stack, resolved_references=resolved_references)
        super(InstructBufferError, self).__init__(msg)

        self.clazz = clazz
        self.attr_name = attr_name


class BufferType(type):
    """Meta class for Buffer classes.
    This meta-class does two things:
      * Copy the fields declared as attributes on the object for "safe keeping" to `__fields__` since they're going to
        get overwritten by actual values once the instance is created. It also sets the field name for each field
        reference since the name is an rvalue (e.g. when evaluating `foo = int_field()` we are unaware of `foo` in the
        scope of `int_field`).
      * If there's no `byte_size` attribute already existing it tries to calculate and add a `byte_size` class
        attribute - this applies only to buffers that have fixed positions.
    """
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
                positions.extend(field.pack_absolute_position_ref.deref(ctx))
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

        # Set to default all fields that don't have a value (we know that since they're still FieldReference objects)
        for field in self._all_fields():
            if isinstance(getattr(self, field.attr_name()), FieldReference):
                setattr(self, field.attr_name(), field.default)

    def pack(self):
        """Packs the object and returns a buffer representing the packed object."""
        fields = self._all_fields()
        ctx = PackContext(self, fields)

        for field in fields:
            if field.pack_if.deref(ctx):
                try:
                    ctx.output_buffer.set(field.pack_ref.deref(ctx), field.pack_absolute_position_ref.deref(ctx))
                except:
                    raise exceptools.chain(InstructBufferError("Pack error occured", ctx, type(self),
                                                               field.attr_name()))

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
                if field.unpack_if.deref(ctx):
                    # TODO: get rid of unpack_after once we use dependencies as we should.
                    for prev_field in field.unpack_after:
                        prev_field.unpack_value_ref.deref(ctx)
                    field.unpack_value_ref.deref(ctx)
                else:
                    setattr(self, field.attr_name(), None)
            except:
                raise exceptools.chain(InstructBufferError("Unpack error occurred", ctx, type(self), field.attr_name()))

        return self.calc_byte_size(ctx)

    def calc_byte_size(self, ctx=None):
        """
        Returns this instance's size. If the size has to be calculated it may require packing some of the fields.
        """
        if ctx is None:
            ctx = PackContext(self, type(self).__fields__)
        return TotalSizeReference().deref(ctx)

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
