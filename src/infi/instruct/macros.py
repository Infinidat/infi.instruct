import functools

#from .struct import Struct, FieldAdapter
#from .struct.const import ConstFieldAdapter
#from .struct.bit import BitFieldListIO, BitIO, BitPaddingIO
#from .struct.lazy import LazyFieldListIO
#from .struct.optional import OptionalFieldAdapter
#from .struct.selector import StructSelectorIO, FuncStructSelectorIO
#from .array import SumSizeArrayIO, FixedSizeArrayIO
#from .padding import *
from .base import *
from .numeric_macros import *
from .string_macros import *
from .mapping_macros import *
from .array_macros import *
from .struct_macros import *

# def Field(name, io, default=None):
#     """
#     Macro helper to create a new `FieldAdapter` used in a `FieldListIO` instance.

#     :param name: name of the field
#     :param io: an I/O instance used to serializer/deserialize this field
#     :param default: default value of the field if not set by user
#     :rtype: FieldAdapter
#     """
#     return FieldAdapter(name, default, io)

# def ConstField(name, value, io=None):
#     """
#     Macro helper to create a new `ConstFieldAdapter` used in a `FieldListIO` instance.

#     This macro can be used in several methods:

#     >>> ConstField("foo", 5, UBInt8)

#     This created a constant field called ``foo`` with a value of 5 and is serialized/deserialized using UBInt8.

#     >>> ConstField("foo", MyStruct(my_field=1, my_other_field=2))

#     This time ``foo`` is set with the ``MyStruct`` instance passed here. Notice that we don't need to pass an I/O
#     argument because the value is an I/O instance by itself.

#     :param name: name of the field
#     :param value: the value to use as a constant
#     :param io: an I/O instance used to serializer/deserialize this field (optional if ``value`` is an I/O by itself)
#     :rtype: FieldAdapter
#     """
#     if io is None:
#         io = value
#     if isinstance(io, Struct):
#         io = io._io_
#     elif not (isinstance(io, Writer) and isinstance(io, AllocatingReader)):
#         raise InstructError("don't know how to serialize const field %s value %s (consider adding an io argument)" %
#                             (name, value))
#     return ConstFieldAdapter(name, value, io)

# def OptionalField(name, io, predicate, default=None):
#     return OptionalFieldAdapter(name, default, io, predicate)

# def BitField(name, size, default=None):
#     return FieldAdapter(name, default, BitIO(size))

# def BitPadding(size):
#     return BitPaddingIO(size)

# def BitFields(*args):
#     return BitFieldListIO(args)

# def BitFlag(name, default=None):
#     return BitField(name, 1, default)

# def SelfPredicate(func):
#     def wrapper(obj, stream, context):
#         return func(context.get('parent', None), obj, stream, context)
#     return wrapper

# # Backward compatibility
# Flag = BitFlag

# def BytePadding(size, char='\x00'):
#     return BytePaddingIO(size, char)

# # Backward compatibility
# Padding = BytePadding

# def Lazy(*args):
#     return LazyFieldListIO(args)

# def StructSelector(key_io, mapping, default=None):
#     return StructSelectorIO(key_io, mapping, default)

# def StructFunc(func):
#     def wrapper(stream, context):
#         return func(context.get('parent', None), stream, context)
#     return wrapper

# def SelectStructByFunc(name, func, min_max_size=None, default=None):
#     return FieldAdapter(name, default, FuncStructSelectorIO(StructFunc(func), min_max_size))

