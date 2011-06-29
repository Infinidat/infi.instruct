import binascii
from StringIO import StringIO

from infi.instruct import *

from utils import *

def test_simple_bits():
    class MyStruct(Struct):
        _fields_ = BitFields( BitField("foo", 3), BitField("bar", 5) )

    assert MyStruct.sizeof() == 1

    obj = MyStruct.create()
    obj.foo = 6
    obj.bar = 5

    serialized_obj = obj_to_string(obj)
    assert serialized_obj == chr(6 + (5 << 3))

    obj = string_to_obj(MyStruct, chr(6 + (5 << 3)))
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

    serialized_obj = obj_to_string(obj)
    obj = string_to_obj(MyStruct, serialized_obj)
    assert obj.foo == 0x1ae
    assert obj.bar == 0x7f
    assert obj.car == 0x1a
