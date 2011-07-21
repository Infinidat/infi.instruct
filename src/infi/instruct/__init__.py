__import__("pkg_resources").declare_namespace(__name__)

from .fields import Struct, FieldAdapter
from .fields.choice import ChoiceFieldAdapter
from .fields.lazy import LazyFieldListSerializer
from .fields.optional import OptionalFieldAdapter
from .fields.padding import BytePaddingSerializer
from .fields.const import ConstFieldAdapter
from .fields.bit import BitFieldListSerializer, BitSerializer, BitPaddingSerializer
from .fields.struct_selector import StructSelectorSerializer
from .serializer import CreatorSerializer
from .serializers.string import *
from .serializers.primitive import *
from .serializers.array import *
from .serializers.dict import *
from .errors import *

from .serializer import ModifierSerializer

def Field(name, serializer, default=None):
    return FieldAdapter(name, default, serializer)

def OptionalField(name, serializer, predicate, default=None):
    return OptionalFieldAdapter(name, default, serializer, predicate)

def ChoiceField(name, choice_func, serializer_map, default=None):
    return ChoiceFieldAdapter(name, default, choice_func, serializer_map.copy())

def Lazy(*args):
    return LazyFieldListSerializer(args)

def Padding(size, char='\x00'):
    return BytePaddingSerializer(size, char)

def ConstField(name, value, serializer=None):
    if serializer is None:
        if isinstance(value, CreatorSerializer):
            serializer = value
        elif isinstance(value, Struct):
            serializer = type(value)._serializer_
        else:
            raise InstructError("cannot implicitly serialize const field %s value %s (consider adding serializer)" %
                                (name, value))
    return ConstFieldAdapter(name, value, serializer)

def DictField(name, dict, value_serializer, default=None):
    return FieldAdapter(name, default, DictSerializer(dict, value_serializer))

def BitField(name, size, default=None):
    return FieldAdapter(name, default, BitSerializer(size))

def BitPadding(size):
    return BitPaddingSerializer(size)

def BitFields(*args):
    return BitFieldListSerializer(args)

def BitFlag(name, default=None):
    return BitField(name, 1, default)

def TotalSizeArray(name, size_serializer, element_serializer, default=None):
    return FieldAdapter(name, default, TotalSizeArraySerializer(size_serializer, element_serializer))

# Backward compatibility
Flag = BitFlag

def FixedSizeArray(name, n, serializer, default=None):
    if default is not None:
        assert len(default) == n
    return FieldAdapter(name, default, FixedSizeArraySerializer(serializer, n))

def FixedSizeString(name, size, default=None, padding='\x00'):
    if default is not None:
        assert len(default) == size
    return FieldAdapter(name, default, FixedSizeStringSerializer(size, padding))

def FixedSizeBuffer(name, size, default=None):
    if default is not None:
        assert len(default) == size
    return FieldAdapter(name, default, FixedSizeBufferSerializer(size))

def VarSizeBuffer(name, size_serializer, default=None):
    return FieldAdapter(name, default, VarSizeBufferSerializer(size_serializer))

# Shortcut to allow users to use either UBInt8 as a serializer (e.g. in an array) or as a field (e.g. UBInt8("foo", 4))
class SerializerWithField(CreatorSerializer):
    def __init__(self, serializer):
        super(SerializerWithField, self).__init__()
        self.serializer = serializer

    def __call__(self, name, default=None):
        return FieldAdapter(name, default, self.serializer)

    def create_from_stream(self, stream, *args, **kwargs):
        return self.serializer.create_from_stream(stream, *args, **kwargs)

    def write_to_stream(self, obj, stream):
        return self.serializer.write_to_stream(obj, stream)

    def to_repr(self, obj):
        return self.serializer.to_repr(obj)

    def min_sizeof(self):
        return self.serializer.min_sizeof()

    def is_fixed_size(self):
        return self.serializer.is_fixed_size()
    
    def sizeof(self, obj):
        return self.serializer.sizeof(obj)

    def validate(self, obj):
        return self.serializer.validate(obj)

__primitive_types__ = [ 'UBInt8', 'UBInt16', 'UBInt32', 'UBInt64',
                        'SBInt8', 'SBInt16', 'SBInt32', 'SBInt64',
                        'ULInt8', 'ULInt16', 'ULInt32', 'ULInt64',
                        'SLInt8', 'SLInt16', 'SLInt32', 'SLInt64',
                        'UNInt8', 'UNInt16', 'UNInt32', 'UNInt64',
                        'SNInt8', 'SNInt16', 'SNInt32', 'SNInt64',
                        'BFloat32', 'LFloat32', 'NFloat32', 'BFloat64', 'LFloat64', 'NFloat64' ]

for t in __primitive_types__:
    v = vars()
    v[t] = SerializerWithField(v["%sSerializer" % t])
