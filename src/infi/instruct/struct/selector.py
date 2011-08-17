from ..base import Marshal, MinMax, ZERO_MIN_MAX, UNBOUNDED_MIN_MAX, EMPTY_CONTEXT
from ..errors import InstructError
from ..utils.read_ahead_stream import ReadAheadStream

from . import Struct

class StructSelectorMarshal(Marshal):
    def __init__(self, key_marshal, mapping, default=None):
        super(StructSelectorMarshal, self).__init__()
        self.key_marshal = key_marshal
        self.mapping = {}
        self.default = default
        
        for key, struct in self.mapping:
            if not isinstance(struct, Struct):
                raise ValueError("mapping key %s must be a subclass of Struct" % key)
            self.mapping[key] = struct

        structs = mapping.values() + ([ self.default ] if self.default is not None else [])

        self.min_max_size = sum([ struct.min_max_sizeof() for struct in structs ], ZERO_MIN_MAX)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        type(obj).write_to_stream(obj, stream, context)
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        rstream = ReadAheadStream(stream)
        
        rstream.set_read_ahead(True)
        key = self.key_marshal.create_from_stream(rstream, context)
        rstream.set_read_ahead(False)
        if key in self.mapping:
            marshal = self.mapping[key]
        else:
            if self.default is not None:
                marshal = self.default
            else:
                raise InstructError("key %s is not mapped an no default" % (self.key_marshal.to_repr(key, context),))

        result = marshal.create_from_stream(rstream, context, *args, **kwargs)
        if not rstream.is_read_ahead_empty():
            raise InstructError("deserialized key %s with type %s but still have bytes in read-ahead buffer" %
                                (self.key_marshal.to_repr(key, context), marshal))
        return result
    
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return type(obj).to_repr(obj, context)
    
    def sizeof(self, obj):
        return type(obj).sizeof(obj)

    def min_max_sizeof(self):
        return self.min_max_size

class FuncStructSelectorMarshal(Marshal):
    def __init__(self, func, min_max_size=UNBOUNDED_MIN_MAX):
        super(FuncStructSelectorMarshal, self).__init__()
        self.func = func
        self.min_max_size = MinMax(min_max_size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        type(obj).write_to_stream(obj, stream, context)
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        rstream = ReadAheadStream(stream)
        
        rstream.set_read_ahead(True)
        
        reader = self.func(rstream, context)

        rstream.set_read_ahead(False)

        result = reader.create_from_stream(rstream, context, *args, **kwargs)
        if not rstream.is_read_ahead_empty():
            raise InstructError("deserialized object %s but still have bytes in read-ahead buffer" %
                                (result.to_repr(context),))
        return result
    
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return type(obj).to_repr(obj, context)
    
    def sizeof(self, obj):
        return type(obj).sizeof(obj)

    def min_max_sizeof(self):
        return self.min_max_size
