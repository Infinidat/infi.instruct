import binascii
from infi.instruct import *

def test_unknown_serializer():
    try:
        class MyStruct(Struct):
            _fields_ = [ ConstField("foo", 0x32) ]
        assert False
    except InstructError:
        pass

def test_serialized_const():
    class MyStruct(Struct):
        _fields_ = [ ConstField("foo", 0x32, UBInt8) ]

    obj = MyStruct()
    assert obj.foo == 0x32, repr(obj.foo)

    obj.foo = 0x32
    
    try:
        obj.foo = 0x12
        assert False
    except InstructError:
        pass

    serialized_obj = MyStruct.write_to_string(obj)
    assert binascii.hexlify(serialized_obj) == "32"

    obj = MyStruct.create_from_string(binascii.unhexlify("32"))
    assert obj.foo == 0x32
