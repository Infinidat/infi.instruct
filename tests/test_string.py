import sys
from infi.instruct.base import Marshal, ReadOnlyContext, EMPTY_CONTEXT, MinMax, UNBOUNDED_MIN_MAX
from infi.instruct.numeric import UBInt8Marshal
from infi.instruct.string import PaddedStringMarshal, VarSizeBufferMarshal
from infi.instruct.struct import Struct
from infi.instruct.string_macros import VarSizeBuffer, FixedSizeString
from infi.instruct.struct.pointer import ReadPointer
from infi.instruct import ULInt8

def test_padded_string_marshal():
    marshal = PaddedStringMarshal(5)
    assert marshal.write_to_string("ad") == "ad\x00\x00\x00"
    assert marshal.create_from_string("ad\x00\x00\x00zxcvzxcv") == "ad"

    marshal = PaddedStringMarshal(5, "a")
    assert marshal.write_to_string("ad") == "adaaa"
    assert marshal.create_from_string("adaaabbbcc") == "ad"

def test_var_size_buffer_marshal_no_sizer():
    class MyOneMarshal(Marshal):
        def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
            stream.write("\x01")

        def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
            return ord(stream.read(1))

    marshal = VarSizeBufferMarshal(MyOneMarshal())
    assert marshal.write_to_string("ad") == "\x01ad"
    assert marshal.create_from_string("\x03abcadsfadsf") == "abc"

def test_var_size_buffer_marshal():
    marshal = VarSizeBufferMarshal(UBInt8Marshal)
    assert marshal.sizeof("asd") == 4
    assert marshal.min_max_sizeof() == MinMax(1, 256)
    assert marshal.write_to_string("ad") == "\x02ad"
    assert marshal.create_from_string("\x03abcadsfadsf") == "abc"

def test_var_size_read_pointer():
    class MyStruct(Struct):
        _fields_ = [ULInt8("length"), VarSizeBuffer("string", ReadPointer("length"))]

    result = MyStruct.create_from_string("\x02hi")
    assert "hi" == result.string

def test_repr_FixedSizeString():
    class MyStruct(Struct):
        _fields_ = [FixedSizeString("test", 5),]

    obj = MyStruct.create_from_string("foo\x00\x00")
    assert 'foo' in repr(obj)
    assert 'foo' in str(obj)

