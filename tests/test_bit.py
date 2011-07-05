import binascii
from infi.instruct import *

def test_simple_bits():
    class MyStruct(Struct):
        _fields_ = BitFields( BitField("foo", 3), BitField("bar", 5) )

    assert MyStruct.sizeof() == 1

    obj = MyStruct.create()
    obj.foo = 6
    obj.bar = 5

    serialized_obj = MyStruct.instance_to_string(obj)
    assert serialized_obj == chr(6 + (5 << 3))

    obj = MyStruct.create_instance_from_string(chr(6 + (5 << 3)))
    assert obj.foo == 6
    assert obj.bar == 5

def test_cross_byte_bits():
    class MyStruct(Struct):
        _fields_ = BitFields( BitField("foo", 9), BitField("bar", 10), BitField("car", 5) )

    assert MyStruct.sizeof() == 3

    obj = MyStruct.create()
    obj.foo = 0x1ae
    obj.bar = 0x7f
    obj.car = 0x1a

    serialized_obj = MyStruct.instance_to_string(obj)
    obj = MyStruct.create_instance_from_string(serialized_obj)
    assert obj.foo == 0x1ae
    assert obj.bar == 0x7f
    assert obj.car == 0x1a
