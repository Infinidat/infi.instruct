from ..base import AllocatingReader, Writer, ReprCapable, Sizer, ApproxSizer, is_sizer, is_approx_sizer, is_repr_capable
from ..base import MinMax, EMPTY_CONTEXT
from ..errors import InstructError
from ..mixin import install_mixin, install_mixin_if
from ..utils.read_ahead_stream import ReadAheadStream

class StructSelectorIO(AllocatingReader, Writer, ReprCapable):
    def __init__(self, key_io, mapping, default=None):
        super(StructSelectorIO, self).__init__()
        self.key_io = key_io
        self.mapping = {}
        self.default = default

        for key, struct in self.mapping:
            self.mapping[key] = struct._io_

        structs = mapping.values() + ([ self.default._io_ ] if self.default is not None else [])
        install_mixin_if(self, Sizer, all([ is_sizer(io) for io in structs ]))

        if all([ is_approx_sizer(io) for io in structs ]):
            install_mixin(self, ApproxSizer)
            min_size = min([ io.min_max_sizeof().min for io in structs ])
            max_size = max([ io.min_max_sizeof().max for io in structs ])
            self.min_max_size = MinMax(min_size, max_size)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        obj.write_to_stream(stream, context)
        
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        rstream = ReadAheadStream(stream)
        
        rstream.set_read_ahead(True)
        key = self.key_io.create_from_stream(rstream, context)
        rstream.set_read_ahead(False)
        if key not in self.mapping and self.default is None:
            raise InstructError("key %s is not mapped an no default" % (self.key_io.to_repr(key, context),))
        io = self.mapping[key]
        result = io.create_from_stream(rstream, context, *args, **kwargs)
        if not rstream.is_read_ahead_empty():
            raise InstructError("deserialized key %s with type %s but still have bytes in read-ahead buffer" %
                                (self.key_io.to_repr(key, context), io))
        return result
    
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return obj.to_repr(context)
    
    def _Sizer_sizeof(self, obj, context=EMPTY_CONTEXT):
        return obj.sizeof(context)

    def _ApproxSizer_min_max_sizeof(self, context=EMPTY_CONTEXT):
        return self.min_max_size
