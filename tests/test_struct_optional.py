import binascii
from infi.instruct import *

def test_optional():
    class MyStruct(Struct):
        def is_foo_exists(obj, stream, context):
            return obj.boo == 0x42
            
        _fields_ = [
            UBInt8("boo"),
            OptionalField("foo", UBInt8, is_foo_exists)
        ]

    obj = MyStruct(boo=1)
    assert obj.boo == 1, obj.boo
    assert obj.foo is None, repr(obj.foo)

    assert MyStruct.write_to_string(obj) == "\x01"

    obj.foo = 0x12
    assert MyStruct.write_to_string(obj) == "\x01\x12"
    
    obj = MyStruct.create_from_string("\x43\x01")
    assert obj.foo is None

    obj = MyStruct.create_from_string("\x42\x01")
    assert obj.foo == 1
