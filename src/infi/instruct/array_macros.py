from .array import *
from .struct import Field

def FixedSizeArray(name, n, element_io, default=None):
    if default is not None:
        assert len(default) == n
    return Field(name, FixedSizeArrayMarshal(n, element_io), default)

def SumSizeArray(name, size_io, element_io, default=None):
    return Field(name, SumSizeArrayMarshal(size_io, element_io), default)

def VarSizeArray(name, size_io, element_io, default=None):
    return Field(name, VarSizeArrayMarshal(size_io, element_io), default)

