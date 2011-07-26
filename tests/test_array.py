import binascii
import sys
from infi.instruct.base import AllocatingReader, Writer, EMPTY_CONTEXT, Sizer, ApproxSizer, MinMax
from infi.instruct.numeric import UBInt8IO, UBInt16IO
from infi.instruct.array import FixedSizeArrayIO, SumSizeArrayIO

def test_fixed_size_array_no_sizer():
    class MyOneIO(AllocatingReader, Writer):
        def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
            stream.write("\x01")

        def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
            return ord(stream.read(1))
    
    io = FixedSizeArrayIO(4, MyOneIO())
    assert not isinstance(io, (Sizer, ApproxSizer))
    assert io.write_to_string([ 1, 2, 3, 4 ]) == "\x01\x01\x01\x01"
    assert io.create_from_string("\x04\x03\x02\x01") == [ 4, 3, 2, 1 ]

def test_fixed_size_array_with_sizer():
    io = FixedSizeArrayIO(4, UBInt8IO)
    assert isinstance(io, (Sizer, ApproxSizer))
    assert io.sizeof([ 1, 2, 3, 4 ]) == 4
    assert io.min_max_sizeof() == MinMax(4, 4)
    assert io.is_fixed_size()
    assert io.write_to_string([ ord('a'), ord('b'), ord('c'), ord('d') ]) == "abcd"
    assert io.create_from_string("abcd") == [ ord('a'), ord('b'), ord('c'), ord('d') ]

def test_sum_size_array():
    io = SumSizeArrayIO(UBInt16IO, UBInt8IO)
    assert isinstance(io, (Sizer, ApproxSizer))
    assert io.sizeof([ 1, 2, 3, 4 ]) == 6
    assert io.min_max_sizeof() == MinMax(2)
    assert not io.is_fixed_size()
    assert io.write_to_string([ ord('a'), ord('b'), ord('c'), ord('d') ]) == "\x00\x04abcd"
    assert io.create_from_string("\x00\x04abcd") == [ ord('a'), ord('b'), ord('c'), ord('d') ]
