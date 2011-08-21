import sys
import types
import collections
from cStringIO import StringIO

class ReadOnlyContext(object):
    """
    Context is a holder of properties that can modify and aid the marshalling process. It is used internally by Instruct
    to communicate additional information between marshalling components and can be used by the user to modify the
    marshalling behavior.
    """
    def __init__(self, d={}):
        self.d = d
        
    def get(self, key, default):
        return self.d.get(key, default)

    def get_dict(self):
        return self.d.copy()

    def writable_copy(self, dict={}):
        c = self.d.copy()
        c.update(dict)
        return WritableContext(c)

    def __repr__(self):
        return "ReadOnlyContext(%s)" % self._shallow_repr()

    def _shallow_repr(self):
        def _is_primitive(obj):
            return isinstance(obj, (types.IntType, types.BooleanType, types.BufferType, types.FloatType, types.ListType,
                                    types.TupleType) + types.StringTypes)
        return ", ".join([ "%s=%s" % (key, repr(val) if _is_primitive(val) else "%s<%s>" % (type(val), id(val)))
                           for key, val in self.d.items() ])

class WritableContext(ReadOnlyContext):
    def __init__(self, d=None):
        self.d = d or {}
    
    def put(self, key, value):
        self.d[key] = value

    def update(self, dict):
        self.d.update(dict)

    def remove(self, key):
        del self.d[key]

    def __repr__(self):
        return "WritableContext(%s)" % self._shallow_repr()

EMPTY_CONTEXT = ReadOnlyContext()

class MinMax(collections.namedtuple('MinMax', 'min max')):
    """
    MinMax is a simple object containing a minimum value and a maximum value. Values are clipped to be [0, sys.maxint].
    You can access the min/max values by the *min* or *max* properties or by index ([0], [1]).
    """
    __slots__ = ()
    
    def __new__(cls, min_val_or_tuple=0, max_val=sys.maxint):
        """
        Initialize a new MinMax instance. This initializer works in four different modes:
         * Copy constructor. If you pass it a MinMax object it'll copy the min/max values.
         * Construct from tuple/list. Construct the min/max by accessing [0] and [1].
         * Construct from a single argument. User provides the min value, max is set to sys.maxint.
         * Construct from two arguments. User provides the min and max values.
        """
        if isinstance(min_val_or_tuple, (list, tuple, MinMax)):
            assert len(min_val_or_tuple) == 2
            min_val, max_val = min_val_or_tuple
        else:
            min_val = min_val_or_tuple
        
        assert min_val <= max_val
        return super(MinMax, cls).__new__(cls, max(0, min_val), min(max_val, sys.maxint))

    def __add__(self, min_max):
        return MinMax(min_max.min + self.min, min_max.max + self.max)

    def is_unbounded(self):
        return self.max >= sys.maxint

    def __str__(self):
        return "MinMax(min=%d, max=%s)" % (self.min, self.max if self.max < sys.maxint else "unbounded")

    def __repr__(self):
        return str(self)

UNBOUNDED_MIN_MAX = MinMax(0, sys.maxint)
ZERO_MIN_MAX = MinMax(0, 0)

class MarshalBase(object):
    def sizeof(self, obj):
        raise NotImplementedError()
    
    # The following methods _should_ be implemented by the user:
    #
    def min_max_sizeof(self):
        return UNBOUNDED_MIN_MAX

    def to_repr(self, obj, context=EMPTY_CONTEXT):
        return repr(obj)

    # The following methods are convenience methods and generally don't need to get overridden:
    #
    def is_fixed_size(self):
        min_max = self.min_max_sizeof()
        return min_max.min == min_max.max

class Marshal(MarshalBase):
    # The following methods _must_ be implemented by the user.
    #
    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        raise NotImplementedError()

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        raise NotImplementedError()

    def sizeof(self, obj):
        raise NotImplementedError()

    # The following methods are convenience methods and generally don't need to get overridden:
    #
    def create_from_string(self, string, context=EMPTY_CONTEXT, *args, **kwargs):
        """
        Deserializes a new instance from a string.
        This is a convenience method that creates a StringIO object and calls create_instance_from_stream().
        """
        io = StringIO(string)
        instance = self.create_from_stream(io, context, *args, **kwargs)
        io.close()
        return instance

    def write_to_string(self, obj, context=EMPTY_CONTEXT):
        io = StringIO()
        instance = self.write_to_stream(obj, io, context)
        result = io.getvalue()
        io.close()
        return result

class FixedSizer(object):
    def sizeof(self, obj):
        return self.size

    def min_max_sizeof(self):
        return MinMax(self.size, self.size)

class ConstReader(FixedSizer, Marshal):
    """
    A marshal that doesn't write to a stream but returns a constant value whenever create_from_stream is called.
    """
    def __init__(self, value):
        self.value = value
        self.size = 0

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return self.value

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        pass

class CallableReader(FixedSizer, Marshal):
    """
    A marshal that doesn't write to a stream but returns a value from a callable whenever create_from_stream is called.
    """
    def __init__(self, func):
        self.func = func
        self.size = 0

    def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
        return self.func(stream, context)

    def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
        pass
