import binascii
from infi.instruct import *

def test_no_fields():
    try:
        class MyStruct(Struct):
            pass
        assert False
    except StructNotWellDefinedError:
        pass

def test_plain_fields_create():
    class MyStruct(Struct):
        _fields_ = [ UBInt8("foo", 0x32), UBInt8("bar", 0x23) ]

    obj = MyStruct()
    assert obj.foo == 0x32
    assert obj.bar == 0x23

    serialized_obj = MyStruct.write_to_string(obj)
    assert binascii.hexlify(serialized_obj) == b"3223"

    obj = MyStruct.create_from_string(binascii.unhexlify("3223"))
    assert obj.foo == 0x32
    assert obj.bar == 0x23
