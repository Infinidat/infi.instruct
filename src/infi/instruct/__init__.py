__import__("pkg_resources").declare_namespace(__name__)

from .fields import Struct, Field, ConstField, Padding
from .fields.lazy import LazyFieldContainer
from .fields.optional import OptionalField
from .fields.bit import BitFieldContainer, BitField, BitPadding
from .serializers.string import FixedSizeStringSerializer
from .errors import *
from .primitive import *

def Lazy(*args):
    return LazyFieldContainer(args)

def BitFields(*args):
    return BitFieldContainer(args)

def Flag(name, default=None):
    return BitField(name, 1, default)

def UBInt8(name, default=None):   return Field(name, UBInt8Serializer, default)
def UBInt16(name, default=None):  return Field(name, UBInt16Serializer, default)
def UBInt32(name, default=None):  return Field(name, UBInt32Serializer, default)
def UBInt64(name, default=None):  return Field(name, UBInt64Serializer, default)
def SBInt8(name, default=None):   return Field(name, SBInt8Serializer, default)
def SBInt16(name, default=None):  return Field(name, SBInt16Serializer, default)
def SBInt32(name, default=None):  return Field(name, SBInt32Serializer, default)
def SBInt64(name, default=None):  return Field(name, SBInt64Serializer, default)
def ULInt8(name, default=None):   return Field(name, ULInt8Serializer, default)
def ULInt16(name, default=None):  return Field(name, ULInt16Serializer, default)
def ULInt32(name, default=None):  return Field(name, ULInt32Serializer, default)
def ULInt64(name, default=None):  return Field(name, ULInt64Serializer, default)
def SLInt8(name, default=None):   return Field(name, SLInt8Serializer, default)
def SLInt16(name, default=None):  return Field(name, SLInt16Serializer, default)
def SLInt32(name, default=None):  return Field(name, SLInt32Serializer, default)
def SLInt64(name, default=None):  return Field(name, SLInt64Serializer, default)
def UNInt8(name, default=None):   return Field(name, UNInt8Serializer, default)
def UNInt16(name, default=None):  return Field(name, UNInt16Serializer, default)
def UNInt32(name, default=None):  return Field(name, UNInt32Serializer, default)
def UNInt64(name, default=None):  return Field(name, UNInt64Serializer, default)
def SNInt8(name, default=None):   return Field(name, SNInt8Serializer, default)
def SNInt16(name, default=None):  return Field(name, SNInt16Serializer, default)
def SNInt32(name, default=None):  return Field(name, SNInt32Serializer, default)
def SNInt64(name, default=None):  return Field(name, SNInt64Serializer, default)
def BFloat32(name, default=None): return Field(name, BFloat32Serializer, default)
def LFloat32(name, default=None): return Field(name, LFloat32Serializer, default)
def NFloat32(name, default=None): return Field(name, NFloat32Serializer, default)
def BFloat64(name, default=None): return Field(name, BFloat64Serializer, default)
def LFloat64(name, default=None): return Field(name, LFloat64Serializer, default)
def NFloat64(name, default=None): return Field(name, NFloat64Serializer, default)
def String(name, size, default=None): return Field(name, FixedSizeStringSerializer(size), default)
