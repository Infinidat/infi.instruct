import types

from .string import *
from .struct import Field

def PaddedString(name, size, padding="\x00", padding_direction=PADDING_DIRECTION_RIGHT, default=None):
    if default is not None and isinstance(size, types.IntType):
        assert len(default) <= size
    return Field(name, PaddedStringMarshal(size, padding, padding_direction), default)

def VarSizeString(name, size_marshal, padding="\x00", padding_direction=PADDING_DIRECTION_RIGHT, default=None):
    return Field(name, VarSizeStringMarshal(size_marshal, padding, padding_direction), default)

# Backward compatibility
FixedSizeString = PaddedString

def FixedSizeBuffer(name, size, default=None):
    if default is not None:
        assert len(default) == size
    return Field(name, FixedSizeBufferMarshal(size), default)

def VarSizeBuffer(name, size_marshal, default=None):
    return Field(name, VarSizeBufferMarshal(size_marshal), default)
