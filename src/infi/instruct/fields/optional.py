from ..base import MinMax, Sizer, ApproxSizer, is_sizer, is_approx_sizer, EMPTY_CONTEXT
from ..mixin import install_mixin_if
from . import FieldAdapter

class OptionalFieldAdapter(FieldAdapter):
    def __init__(self, name, default, io, predicate):
        super(OptionalFieldAdapter, self).__init__(name, default, io)
        self.predicate = predicate
        install_mixin_if(self, Sizer, is_sizer(io))
        install_mixin_if(self, ApproxSizer, is_approx_sizer(io))

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        value = getattr(obj, self.name, self.default)
        if value is not None:
            super(OptionalFieldAdapter, self).write_to_stream(obj, stream, context)

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        if self.predicate(obj, stream, context):
            super(OptionalFieldAdapter, self).read_into_from_stream(obj, stream, context, *args, **kwargs)

    def _ApproxSizer_min_max_sizeof(self, context=EMPTY_CONTEXT):
        return MinMax(0, self.io.min_max_sizeof(context).max)

    def _Sizer_sizeof(self, obj, context=EMPTY_CONTEXT):
        value = getattr(obj, self.name, self.default)
        if value is None:
            return 0
        return self.io.sizeof(value, context)
