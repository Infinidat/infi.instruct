from infi.pyutils.mixin import install_mixin_if

from ..base import MinMax, Sizer, ApproxSizer, is_sizer, is_approx_sizer, EMPTY_CONTEXT
from . import FieldAdapter

class OptionalFieldAdapter(FieldAdapter):
    class MySizer(Sizer):
        def sizeof(self, obj, context=EMPTY_CONTEXT):
            value = getattr(obj, self.name, self.default)
            if value is None:
                return 0
            return self.io.sizeof(value, context)

    class MyApproxSizer(ApproxSizer):
        def min_max_sizeof(self, context=EMPTY_CONTEXT):
            return MinMax(0, self.io.min_max_sizeof(context).max)

    def __init__(self, name, default, io, predicate):
        super(OptionalFieldAdapter, self).__init__(name, default, io)
        self.predicate = predicate
        install_mixin_if(self, OptionalFieldAdapter.MySizer, is_sizer(io))
        install_mixin_if(self, OptionalFieldAdapter.MyApproxSizer, is_approx_sizer(io))

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        value = getattr(obj, self.name, self.default)
        if value is not None:
            super(OptionalFieldAdapter, self).write_to_stream(obj, stream, context)

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        if self.predicate(obj, stream, context):
            super(OptionalFieldAdapter, self).read_into_from_stream(obj, stream, context, *args, **kwargs)
