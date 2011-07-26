import sys
from infi.instruct.base import AllocatingReader, Writer, EMPTY_CONTEXT
from infi.instruct.base import Sizer, ApproxSizer, ReadOnlyContext, UNBOUNDED_MIN_MAX, MinMax
from infi.instruct.numeric import UBInt8IO
from infi.instruct.string import PaddedStringIO, VarSizeBufferIO

def test_padded_string_io():
    io = PaddedStringIO(5)
    assert io.write_to_string("ad") == "ad\x00\x00\x00"
    assert io.create_from_string("ad\x00\x00\x00zxcvzxcv") == "ad"

    io = PaddedStringIO(5, "a")
    assert io.write_to_string("ad") == "adaaa"
    assert io.create_from_string("adaaabbbcc") == "ad"

def test_var_size_buffer_io_no_sizer():
    class MyOneIO(AllocatingReader, Writer):
        def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
            stream.write("\x01")

        def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
            return ord(stream.read(1))

    io = VarSizeBufferIO(MyOneIO())
    assert not isinstance(io, (Sizer, ApproxSizer))
    assert io.write_to_string("ad") == "\x01ad"
    assert io.create_from_string("\x03abcadsfadsf") == "abc"
    
def test_var_size_buffer_io():
    io = VarSizeBufferIO(UBInt8IO)
    assert isinstance(io, (Sizer, ApproxSizer))
    assert io.sizeof("asd") == 4
    assert io.min_max_sizeof() == MinMax(1, sys.maxint)
    assert io.write_to_string("ad") == "\x02ad"
    assert io.create_from_string("\x03abcadsfadsf") == "abc"
