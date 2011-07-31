import functools

from .fields import Struct, FieldAdapter
from .fields.const import ConstFieldAdapter
from .fields.bit import BitFieldListIO, BitIO, BitPaddingIO
from .fields.lazy import LazyFieldListIO
from .fields.optional import OptionalFieldAdapter
from .fields.selector import StructSelectorIO
from .array import SumSizeArrayIO, FixedSizeArrayIO
from .mapping import *
from .padding import *
from .base import *
from .numeric import *
from .string import *

def Field(name, io, default=None):
    return FieldAdapter(name, default, io)

def ConstField(name, value, io=None):
    if io is None:
        io = value
    if isinstance(io, Struct):
        io = io._io_
    elif not (isinstance(io, Writer) and isinstance(io, AllocatingReader)):
        raise InstructError("don't know how to serialize const field %s value %s (consider adding an io argument)" %
                            (name, value))
    return ConstFieldAdapter(name, value, io)

def OptionalField(name, io, predicate, default=None):
    return OptionalFieldAdapter(name, default, io, predicate)

def MappingField(name, value_io, dict, default=None):
    return FieldAdapter(name, default, MappingIO(dict, value_io))

def BitField(name, size, default=None):
    return FieldAdapter(name, default, BitIO(size))

def BitPadding(size):
    return BitPaddingIO(size)

def BitFields(*args):
    return BitFieldListIO(args)

def BitFlag(name, default=None):
    return BitField(name, 1, default)

def SelfPredicate(func):
    def wrapper(obj, stream, context):
        return func(context.get('parent', None), obj, stream, context)
    return wrapper

# Backward compatibility
Flag = BitFlag

def BytePadding(size, char='\x00'):
    return BytePaddingIO(size, char)

# Backward compatibility
Padding = BytePadding

def FixedSizeArray(name, n, element_io, default=None):
    if default is not None:
        assert len(default) == n
    return FieldAdapter(name, default, FixedSizeArrayIO(n, element_io))

def SumSizeArray(name, size_io, element_io, default=None):
    return FieldAdapter(name, default, SumSizeArrayIO(size_io, element_io))

def PaddedString(name, size, padding="\x00", default=None):
    if default is not None:
        assert len(default) == size
    return FieldAdapter(name, default, PaddedStringIO(size, padding))

# Backward compatibility
FixedSizeString = PaddedString

def FixedSizeBuffer(name, size, default=None):
    if default is not None:
        assert len(default) == size
    return FieldAdapter(name, default, FixedSizeBufferIO(size))

def VarSizeBuffer(name, size_io, default=None):
    return FieldAdapter(name, default, VarSizeBufferIO(size_io))

def Lazy(*args):
    return LazyFieldListIO(args)

def StructSelector(key_io, mapping, default=None):
    return StructSelectorIO(key_io, mapping, default)

# Shortcut to allow users to use either UBInt8 as a serializer (e.g. in an array) or as a field (e.g. UBInt8("foo", 4))
class IOWithField(AllocatingReader, Writer, Sizer, ApproxSizer, ReprCapable):
    def __init__(self, io):
        super(IOWithField, self).__init__()
        self.io = io

    def __call__(self, name, default=None):
        return FieldAdapter(name, default, self.io)

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return self.io.create_from_stream(stream, context, *args, **kwargs)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        return self.io.write_to_stream(obj, stream, context)

    def sizeof(self, obj, context=EMPTY_CONTEXT):
        return self.io.sizeof(obj, context)

    def min_max_sizeof(self, context=EMPTY_CONTEXT):
        return self.io.min_max_sizeof(context)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return self.io.to_repr(obj, context)

__primitive_types__ = [ 'UBInt8', 'UBInt16', 'UBInt32', 'UBInt64',
                        'SBInt8', 'SBInt16', 'SBInt32', 'SBInt64',
                        'ULInt8', 'ULInt16', 'ULInt32', 'ULInt64',
                        'SLInt8', 'SLInt16', 'SLInt32', 'SLInt64',
                        'UNInt8', 'UNInt16', 'UNInt32', 'UNInt64',
                        'SNInt8', 'SNInt16', 'SNInt32', 'SNInt64',
                        'BFloat32', 'LFloat32', 'NFloat32', 'BFloat64', 'LFloat64', 'NFloat64' ]

for t in __primitive_types__:
    v = vars()
    v[t] = IOWithField(v["%sIO" % t])
