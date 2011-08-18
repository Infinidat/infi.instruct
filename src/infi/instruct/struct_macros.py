import types

from .struct import Struct, Field, AnonymousField
from .struct.optional import OptionalField
from .struct.const import ConstField as OrigConstField
from .struct.bit import BitFieldListContainer, BitMarshal, BitPaddingMarshal
from .struct.bit import PositionalBitMarshal, PositionalBitFieldListContainer
from .struct.lazy import LazyFieldListContainer
from .struct.selector import StructSelectorMarshal, FuncStructSelectorMarshal
from .struct.pointer import ReadPointer

from .base import Marshal, UNBOUNDED_MIN_MAX
from .errors import InstructError
from .padding import BytePaddingMarshal

def ConstField(name, value, marshal=None):
    """
    This macro can be used in several methods:

    >>> ConstField("foo", 5, UBInt8)

    This created a constant field called ``foo`` with a value of 5 and is serialized/deserialized using UBInt8.

    >>> ConstField("foo", MyStruct(my_field=1, my_other_field=2))

    This time ``foo`` is set with the ``MyStruct`` instance passed here. Notice that we don't need to pass an I/O
    argument because the value is an I/O instance by itself.

    :param name: name of the field
    :param value: the value to use as a constant
    :param marshal: a marshal instance to serialize/deserialize this field (optional if ``value`` is a marshal)
    :rtype: Field
    """
    if marshal is None:
        marshal = value
    if isinstance(marshal, Struct):
        marshal = type(marshal)
    elif not isinstance(marshal, Marshal):
        raise InstructError("don't know how to serialize const field %s value %s (consider adding a marshal argument)" %
                            (name, value))
    return OrigConstField(name, marshal, value)

def BitFields(*args):
    if any([ isinstance(field.marshal, PositionalBitMarshal) for field in args ]):
        assert all([ isinstance(field.marshal, PositionalBitMarshal) for field in args ])
        return PositionalBitFieldListContainer(None, args)
    else:
        return BitFieldListContainer(args)

def BitField(name, size, default=None):
    if isinstance(size, (types.TupleType, types.ListType, slice)):
        return Field(name, PositionalBitMarshal((size,) if isinstance(size, slice) else size), default)
    return Field(name, BitMarshal(size), default)

def BitFlag(name, default=None):
    return Field(name, BitMarshal(1), default)

def BitPadding(size):
    return AnonymousField(BitPaddingMarshal(size))

def BytePadding(size, char='\x00'):
    return AnonymousField(BytePaddingMarshal(size, char))

class BitSlicer(object):
    def __getitem__(self, key):
        if isinstance(key, (types.TupleType, types.ListType)):
            return list(key)
        elif isinstance(key, slice):
            return [ key ]

Bits = BitSlicer()

def Lazy(*args):
    return LazyFieldListContainer(args)

# Backward compatibility
Padding = BytePadding

def StructSelector(key_marshal, mapping, default=None):
    return StructSelectorMarshal(key_marshal, mapping, default)

def StructFunc(func):
    def wrapper(stream, context):
        return func(context.get('struct', None), stream, context)
    return wrapper

def SelectStructByFunc(name, func, min_max_size=UNBOUNDED_MIN_MAX, default=None):
    return Field(name, FuncStructSelectorMarshal(StructFunc(func), min_max_size), default)
