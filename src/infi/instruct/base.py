import sys
from cStringIO import StringIO

class ReadOnlyContext(object):
    def __init__(self, d={}):
        self.d = d
        
    def get(self, key, default):
        return self.d.get(key, default)

    def writable_copy(self, dict={}):
        c = self.d.copy()
        c.update(dict)
        return WritableContext(c)

class WritableContext(ReadOnlyContext):
    def __init__(self, d=None):
        self.d = d or {}
    
    def put(self, key, value):
        self.d[key] = value

    def remove(self, key):
        del self.d[key]

EMPTY_CONTEXT = ReadOnlyContext()

class MinMax(object):
    def __init__(self, min_val, max_val=sys.maxint):
        self.min = max(0, min_val)
        self.max = min(max_val, sys.maxint)

    def add(self, min_max):
        return MinMax(min(min_max.min + self.min, sys.maxint), min(sys.maxint, min_max.max + self.max))

    def is_unbounded(self):
        return self.max >= sys.maxint

    def __eq__(self, obj):
        return self.min == obj.min and self.max == obj.max

    def __str__(self):
        return "MinMax(min=%d, max=%s)" % (self.min, self.max if self.max < sys.maxint else "unbounded")

    def __repr__(self):
        return str(self)

    @classmethod
    def from_argument(cls, arg):
        if arg is None or isinstance(arg, MinMax):
            return arg
        elif isinstance(arg, (tuple, list)):
            assert len(arg) == 2
            return MinMax(arg[0], arg[1])
        raise ValueError("from_argument expects a MinMax object or a pair")

UNBOUNDED_MIN_MAX = MinMax(0, sys.maxint)

class AllocatingReader(object):
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        raise NotImplementedError()

    def create_from_string(self, string, context=EMPTY_CONTEXT, *args, **kwargs):
        """
        Deserializes a new instance from a string.
        This is a convenience method that creates a StringIO object and calls create_instance_from_stream().
        """
        io = StringIO(string)
        instance = self.create_from_stream(io, context, *args, **kwargs)
        io.close()
        return instance

class MutatingReader(object):
    def read_into_from_stream(self, obj, stream, context=EMPTY_CONTEXT):
        raise NotImplementedError()

    def read_into_from_string(self, obj, string, context=EMPTY_CONTEXT):
        """
        Reads attributes into obj from a string.
        This is a convenience method that creates a StringIO object and calls read_into_from_stream().
        """
        io = StringIO(string)
        instance = self.read_into_from_stream(obj, io, context)
        io.close()

class Writer(object):
    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        raise NotImplementedError()

    def write_to_string(self, obj, context=EMPTY_CONTEXT):
        io = StringIO()
        instance = self.write_to_stream(obj, io, context)
        result = io.getvalue()
        io.close()
        return result

class Sizer(object):
    def sizeof(self, obj, context=EMPTY_CONTEXT):
        raise NotImplementedError()

class ApproxSizer(object):
    def min_max_sizeof(self, context=EMPTY_CONTEXT):
        raise NotImplementedError()

    def is_fixed_size(self, context=EMPTY_CONTEXT):
        min_max = self.min_max_sizeof(context)
        return min_max.min == min_max.max

class ReprCapable(object):
    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

    @classmethod
    def to_repr(cls, io, obj, context=EMPTY_CONTEXT):
        if isinstance(io, ReprCapable):
            return io.to_repr(obj, context)
        else:
            return repr(obj)

class FixedSizer(ApproxSizer):
    def sizeof(self, obj, context=EMPTY_CONTEXT):
        return self.size

    def min_max_sizeof(self, context=EMPTY_CONTEXT):
        return MinMax(self.size, self.size)

def is_repr_capable(obj):
    return hasattr(obj, 'to_repr')

def is_sizer(obj):
    return hasattr(obj, 'sizeof')

def is_approx_sizer(obj):
    return hasattr(obj, 'min_max_sizeof')
