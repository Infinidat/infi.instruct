import binascii
from infi.instruct import *

def test_plain_fields_create():
    class MyStruct(Struct):
        _fields_ = [ FixedSizeArray("foo", 4, UBInt8), UBInt8("bar", 0x23) ]

    obj = MyStruct()
    assert obj.bar == 0x23
    assert obj.sizeof() == 4 + 1

    obj.foo = [ 1, 2, 3, 4 ]

    serialized_obj = MyStruct.to_string(obj)
    assert binascii.hexlify(serialized_obj) == "0102030423"

    obj = MyStruct.create_from_string(binascii.unhexlify("0403020123"))
    assert obj.foo == [ 4, 3, 2, 1 ]
    assert obj.bar == 0x23
