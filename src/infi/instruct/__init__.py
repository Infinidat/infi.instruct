__import__("pkg_resources").declare_namespace(__name__)

from .fields import Struct, Field, ConstField, Padding
from .fields.switch import MultiTypeSwitchField, DictSwitchField
from .fields.lazy import LazyFieldContainer
from .fields.optional import OptionalField
from .fields.bit import BitFieldContainer, BitField, BitPadding
from .serializers.string import *
from .serializers.primitive import *
from .serializers.array import *
from .errors import *

def Lazy(*args):
    return LazyFieldContainer(args)

def BitFields(*args):
    return BitFieldContainer(args)

def Flag(name, default=None):
    return BitField(name, 1, default)

def FixedSizeArray(name, n, serializer, default=None):
    if default is not None:
        assert len(default) == n
    return Field(name, FixedSizeArraySerializer(n, serializer), default)

def FixedSizeString(name, size, default=None):
    if default is not None:
        assert len(default) == size
    return Field(name, FixedSizeStringSerializer(size), default)

# Shortcut to allow users to use either UBInt8 as a serializer (e.g. in an array) or as a field (e.g. UBInt8("foo", 4))
class SerializerWithField(DynamicSerializer):
    def __init__(self, serializer):
        super(SerializerWithField, self).__init__()
        self.serializer = serializer

    def __call__(self, name, default=None):
        return Field(name, self.serializer, default)

    def create_instance_from_stream(self, stream, *args, **kwargs):
        return self.serializer.create_instance_from_stream(stream, *args, **kwargs)

    def write_instance_to_stream(self, instance, stream):
        return self.serializer.write_instance_to_stream(instance, stream)

    def instance_repr(self, instance):
        return self.serializer.instance_repr(instance)

    def sizeof(self):
        return self.serializer.sizeof()

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
