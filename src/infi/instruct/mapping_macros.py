from .mapping import *
from .struct import Field

def MappingField(name, value_marshal, dict, default=None):
    return Field(name, FixedSizeMappingMarshal(dict, value_marshal), default)
