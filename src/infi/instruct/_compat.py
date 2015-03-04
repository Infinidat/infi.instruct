import sys

PY2 = sys.version_info[0] == 2

if PY2:

    from cStringIO import StringIO
    import types

    STRING_TYPES = types.StringTypes

    def pad(c, n):
        assert type(c) is str
        return c * n

    range = xrange

    long = long

    def is_string_or_bytes(obj):
        return isinstance(obj, basestring)

    def values_list(d):
        return d.values()

else:
    from itertools import repeat
    from io import BytesIO as StringIO

    STRING_TYPES = (bytes, str)

    def pad(c, n):
        assert type(c) is int
        return bytes(repeat(c, n))

    range = range
    long = int

    def is_string_or_bytes(obj):
        return isinstance(obj, (bytes, str))

    def values_list(d):
        return list(d.values())
