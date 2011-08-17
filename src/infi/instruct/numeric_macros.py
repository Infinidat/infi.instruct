from .numeric import *
from .base import Marshal
from .struct import Field

# Shortcut to allow users to use either UBInt8 as a serializer (e.g. in an array) or as a field (e.g. UBInt8("foo", 4))
class MarshalWithField(Marshal):
    def __init__(self, marshal):
        super(MarshalWithField, self).__init__()
        self.marshal = marshal

    def __call__(self, name, default=None):
        return Field(name, self.marshal, default)

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return self.marshal.create_from_stream(stream, context, *args, **kwargs)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        return self.marshal.write_to_stream(obj, stream, context)

    def sizeof(self, obj):
        return self.marshal.sizeof(obj)

    def min_max_sizeof(self):
        return self.marshal.min_max_sizeof()

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return self.marshal.to_repr(obj, context)

__primitive_types__ = [ 'UBInt8', 'UBInt16', 'UBInt32', 'UBInt64',
                        'SBInt8', 'SBInt16', 'SBInt32', 'SBInt64',
                        'ULInt8', 'ULInt16', 'ULInt32', 'ULInt64',
                        'SLInt8', 'SLInt16', 'SLInt32', 'SLInt64',
                        'UNInt8', 'UNInt16', 'UNInt32', 'UNInt64',
                        'SNInt8', 'SNInt16', 'SNInt32', 'SNInt64',
                        'BFloat32', 'LFloat32', 'NFloat32', 'BFloat64', 'LFloat64', 'NFloat64' ]

for t in __primitive_types__:
    v = vars()
    v[t] = MarshalWithField(v["%sMarshal" % t])
