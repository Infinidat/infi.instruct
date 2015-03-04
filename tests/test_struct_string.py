import sys
from infi.instruct.base import Marshal, ReadOnlyContext, EMPTY_CONTEXT, MinMax, UNBOUNDED_MIN_MAX
from infi.instruct.numeric import UBInt8Marshal
from infi.instruct.string import PaddedStringMarshal, VarSizeBufferMarshal
from infi.instruct.struct import Struct
from infi.instruct.string_macros import VarSizeBuffer, FixedSizeString
from infi.instruct.struct.pointer import ReadPointer
from infi.instruct import ULInt8
from infi.instruct._compat import PY2

def test_padded_string_marshal():
    marshal = PaddedStringMarshal(5)
    assert marshal.write_to_string(b"ad") == b"ad\x00\x00\x00"
    assert marshal.create_from_string(b"ad\x00\x00\x00zxcvzxcv") == b"ad"

    marshal = PaddedStringMarshal(5, b"a")
    assert marshal.write_to_string(b"ad") == b"adaaa"
    assert marshal.create_from_string(b"adaaabbbcc") == b"ad"

def test_var_size_buffer_marshal_no_sizer():
    class MyOneMarshal(Marshal):
        def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
            stream.write(b"\x01")

        def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
            return ord(stream.read(1))

    marshal = VarSizeBufferMarshal(MyOneMarshal())
    assert marshal.write_to_string(b"ad") == b"\x01ad"
    assert marshal.create_from_string(b"\x03abcadsfadsf") == b"abc"

def test_var_size_buffer_marshal():
    marshal = VarSizeBufferMarshal(UBInt8Marshal)
    assert marshal.sizeof(b"asd") == 4
    assert marshal.min_max_sizeof() == MinMax(1, 256)
    assert marshal.write_to_string(b"ad") == b"\x02ad"
    assert marshal.create_from_string(b"\x03abcadsfadsf") == b"abc"

def test_var_size_read_pointer():
    class MyStruct(Struct):
        _fields_ = [ULInt8("length"), VarSizeBuffer("string", ReadPointer("length"))]

    result = MyStruct.create_from_string(b"\x02hi")
    assert b"hi" == result.string

def test_repr_FixedSizeString():
    class MyStruct(Struct):
        _fields_ = [FixedSizeString("test", 5),]

    obj = MyStruct.create_from_string(b"foo\x00\x00")
    assert 'foo' in repr(obj)
    if PY2:
        assert 'foo' in str(obj)

    assert b'foo' in obj.to_bytes()

