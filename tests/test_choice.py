import binascii
from infi.instruct import *

class Struct1(Struct):
    _fields_ = [
        UBInt8("foo"),
        UBInt32("bar")
    ]

class Struct2(Struct):
    _fields_ = [
        UBInt8("foo1"),
        UBInt8("bar1"),
        UBInt8("car1")
    ]

class Struct3(Struct):
    def _choose_obj_type(self):
        return self.type
    
    _fields_ = [
        UBInt8("type"),
        ChoiceField("obj", _choose_obj_type, {
            1: Struct1,
            2: Struct2
        })
    ]

def test_choice():
    s = Struct3.create()
    s.type = 1
    s.obj = Struct1.create(foo=1, bar=2)
    serialized_s = Struct3.instance_to_string(s)
    assert serialized_s == binascii.unhexlify("010100000002")

    s2 = Struct3.create_instance_from_string(serialized_s)
    assert s2.type == 1
    assert isinstance(s2.obj, Struct1)
    assert s2.obj.foo == 1
    assert s2.obj.bar == 2

    s3 = Struct3.create_instance_from_string(binascii.unhexlify("02010203"))
    assert s3.type == 2
    assert isinstance(s3.obj, Struct2)
    assert s3.obj.foo1 == 1
    assert s3.obj.bar1 == 2
    assert s3.obj.car1 == 3
