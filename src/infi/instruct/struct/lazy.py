from cStringIO import StringIO
from infi.pyutils.mixin import install_mixin_if

from . import FieldAdapter, FieldListIO
from ..base import FixedSizer, Sizer, ApproxSizer, is_sizer, is_approx_sizer, EMPTY_CONTEXT

class LazyFieldDecorator(FieldAdapter):
    class MySizer(Sizer):
        def sizeof(self, obj, context=EMPTY_CONTEXT):
            return self.field.min_max_sizeof(obj, context)
        
    class MyApproxSizer(ApproxSizer):
        def min_max_sizeof(self, context=EMPTY_CONTEXT):
            return self.field.min_max_sizeof(context)

    def __init__(self, container, field):
        super(LazyFieldDecorator, self).__init__(field.name, field.default, field.io)
        self.container = container
        self.field = field
        install_mixin_if(self, LazyFieldDecorator.MySizer, is_sizer(self.field))
        install_mixin_if(self, LazyFieldDecorator.MyApproxSizer, is_approx_sizer(self.field))

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        self.field.write_to_stream(obj, stream, context)

    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        self.field.read_into_from_stream(obj, stream, context, *args, **kwargs)
        
    def __set__(self, instance, value):
        self.container.instantiate_if_needed(instance)
        self.field.__set__(instance, value)
    
    def __get__(self, instance, owner):
        self.container.instantiate_if_needed(instance)
        return self.field.__get__(instance, owner)

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        if self.container.is_instantiated(obj):
            return self.field.to_repr(obj, context)
        return "<lazy>"

class LazyFieldListIO(FixedSizer, FieldListIO):
    def __init__(self, ios):
        new_ios = []
        for io in ios:
            if not is_approx_sizer(io) or not io.is_fixed_size():
                raise ValueError("%s is not a fixed-size field inside a lazy container" % (io,))
            if isinstance(io, FieldAdapter):
                new_ios.append(LazyFieldDecorator(self, io))
            else:
                new_ios.append(io)
        
        super(LazyFieldListIO, self).__init__(new_ios)

        self.size = sum([ io.min_max_sizeof().min for io in self.ios ])
        self.lazy_key = "_lazy_container_%s" % id(self)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        self.instantiate_if_needed(obj)
        super(LazyFieldListIO, self).write_to_stream(obj, stream)

    def read_from_stream(self, obj, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        data = stream.read(self.size)
        setattr(obj, self.lazy_key, dict(data=data, context=context, args=args, kwargs=kwargs))

    def is_instantiated(self, obj):
        return hasattr(obj, self.lazy_key)

    def instantiate_if_needed(self, obj):
        if self.is_instantiated(obj):
            return
        params = getattr(obj, self.lazy_key)
        stream = StringIO(params['data'])
        try:
            super(LazyFieldListIO, self).read_from_stream(obj, stream, params['context'],
                                                          *params['args'], **params['kwargs'])
        finally:
            delattr(obj, self.lazy_key)
