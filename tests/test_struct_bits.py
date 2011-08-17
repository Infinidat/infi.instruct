import binascii
from infi.instruct import *

def test_simple_bits():
    class MyStruct(Struct):
        _fields_ = BitFields( BitField("foo", 3), BitField("bar", 5) )

    assert MyStruct.min_max_sizeof() == MinMax(1, 1), MyStruct.min_max_sizeof()

    obj = MyStruct()
    obj.foo = 6
    obj.bar = 5

    serialized_obj = MyStruct.write_to_string(obj)
    assert serialized_obj == chr(6 + (5 << 3)), repr(serialized_obj)

    obj = MyStruct.create_from_string(chr(6 + (5 << 3)))
    assert obj.foo == 6
    assert obj.bar == 5
    assert MyStruct.sizeof(obj) == 1

def test_cross_byte_bits():
    class MyStruct(Struct):
        _fields_ = BitFields( BitField("foo", 9), BitField("bar", 10), BitField("car", 5) )

    assert MyStruct.min_max_sizeof() == MinMax(3, 3), MyStruct.min_max_sizeof()

    obj = MyStruct()
    obj.foo = 0x1ae
    obj.bar = 0x7f
    obj.car = 0x1a

    serialized_obj = MyStruct.write_to_string(obj)
    obj = MyStruct.create_from_string(serialized_obj)
    assert obj.foo == 0x1ae
    assert obj.bar == 0x7f
    assert obj.car == 0x1a
    assert MyStruct.sizeof(obj) == 3

def test_bit_padding():
    class MyStruct(Struct):
        _fields_ = BitFields( BitField("foo", 4), BitPadding(4) )

    assert MyStruct.min_max_sizeof() == MinMax(1, 1), MyStruct.min_max_sizeof()

    obj = MyStruct()
    obj.foo = 0x0a

    serialized_obj = MyStruct.write_to_string(obj)
    obj = MyStruct.create_from_string(serialized_obj)
    assert obj.foo == 0x0a
    assert MyStruct.sizeof(obj) == 1
