import binascii
from StringIO import StringIO

from infi.instruct import *

from utils import *

def test_no_fields():
    class MyStruct(Struct):
        pass
    try:
        MyStruct.create()
        assert False
    except StructNotWellDefinedError:
        pass

def test_plain_fields_create():
    class MyStruct(Struct):
        _fields_ = [ UBInt8("foo", 0x32), UBInt8("bar", 0x23) ]

    obj = MyStruct.create()
    assert obj.foo == 0x32
    assert obj.bar == 0x23

    serialized_obj = obj_to_string(obj)
    assert binascii.hexlify(serialized_obj) == "3223"

    obj = string_to_obj(MyStruct, binascii.unhexlify("3223"))
    assert obj.foo == 0x32
    assert obj.bar == 0x23
