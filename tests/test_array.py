import binascii
import sys
from infi.instruct.base import Marshal, EMPTY_CONTEXT, MinMax
from infi.instruct.numeric import UBInt8Marshal, UBInt16Marshal
from infi.instruct.array import FixedSizeArrayMarshal, SumSizeArrayMarshal

def test_fixed_size_array_no_sizer():
    class MyOneMarshal(Marshal):
        def write_to_stream(self, obj, stream, context=EMPTY_CONTEXT):
            stream.write("\x01")

        def create_from_stream(self, stream, context=EMPTY_CONTEXT, *args, **kwargs):
            return ord(stream.read(1))
    
    io = FixedSizeArrayMarshal(4, MyOneMarshal())
    assert io.write_to_string([ 1, 2, 3, 4 ]) == "\x01\x01\x01\x01"
    assert io.create_from_string("\x04\x03\x02\x01") == [ 4, 3, 2, 1 ]

def test_fixed_size_array_with_sizer():
    io = FixedSizeArrayMarshal(4, UBInt8Marshal)
    assert io.sizeof([ 1, 2, 3, 4 ]) == 4
    assert io.min_max_sizeof() == MinMax(4, 4)
    assert io.is_fixed_size()
    assert io.write_to_string([ ord('a'), ord('b'), ord('c'), ord('d') ]) == "abcd"
    assert io.create_from_string("abcd") == [ ord('a'), ord('b'), ord('c'), ord('d') ]

def test_sum_size_array():
    io = SumSizeArrayMarshal(UBInt16Marshal, UBInt8Marshal)
    assert io.sizeof([ 1, 2, 3, 4 ]) == 6
    assert io.min_max_sizeof() == MinMax(2, (2 ** 16 - 1) + 2), io.min_max_sizeof()
    assert not io.is_fixed_size()
    assert io.write_to_string([ ord('a'), ord('b'), ord('c'), ord('d') ]) == "\x00\x04abcd"
    assert io.create_from_string("\x00\x04abcd") == [ ord('a'), ord('b'), ord('c'), ord('d') ]
