from infi.instruct.errors import InstructError
from infi.instruct.struct import Struct
from infi.instruct.macros import StructFunc, SelectStructByFunc, UBInt8, FixedSizeArray, ConstField
from infi.instruct.struct.selector import FuncStructSelectorMarshal

def test_simple():
    PolyHeaderFields = [ UBInt8("type"), UBInt8("size") ]

    class PolyStructHeader(Struct):
        _fields_ = PolyHeaderFields

    class PolyStruct1(Struct):
        _fields_ = PolyHeaderFields + [ UBInt8("foo"), UBInt8("bar") ]

    class PolyStruct2(Struct):
        _fields_ = PolyHeaderFields + [ UBInt8("coo") ]

    class MyStruct(Struct):
        def _determine_type(self, stream, context=None):
            header = PolyStructHeader.create_from_stream(stream, context)
            if header.type == 1:
                return PolyStruct1
            elif header.type == 2:
                return PolyStruct2
            raise InstructError("unknown poly type: %d" % header.type)

        _fields_ = [ SelectStructByFunc("poly_field", _determine_type, (0, 255)) ]

    s = MyStruct(poly_field=PolyStruct1(type=1, size=4, foo=1, bar=2))
    assert str(s) == "\x01\x04\x01\x02"

    s = MyStruct.create_from_string("\x01\x04\x01\x02")
    assert isinstance(s.poly_field, PolyStruct1)
    assert s.poly_field.type == 1
    assert s.poly_field.size == 4
    assert s.poly_field.foo == 1
    assert s.poly_field.bar == 2
    
    s = MyStruct.create_from_string("\x02\x03\x03")
    assert isinstance(s.poly_field, PolyStruct2)
    assert s.poly_field.type == 2
    assert s.poly_field.size == 3
    assert s.poly_field.coo == 3

def test_array():
    class PolyStructHeader(Struct):
        _fields_ = [ UBInt8("type"), UBInt8("size") ]

    class PolyStruct1(Struct):
        _fields_ = [ ConstField("type", 1, UBInt8), ConstField("size", 4, UBInt8), UBInt8("foo"), UBInt8("bar") ]

    class PolyStruct2(Struct):
        _fields_ = [ ConstField("type", 2, UBInt8), ConstField("size", 3, UBInt8), UBInt8("coo") ]

    class MyStruct(Struct):
        def _determine_type(self, stream, context=None):
            header = PolyStructHeader.create_from_stream(stream, context)
            if header.type == 1:
                return PolyStruct1
            elif header.type == 2:
                return PolyStruct2
            raise InstructError("unknown poly type: %d" % header.type)

        _fields_ = [ FixedSizeArray("my_array", 3, FuncStructSelectorMarshal(StructFunc(_determine_type), (0, 255))) ]

    s = MyStruct(my_array=[ PolyStruct1(foo=1, bar=2), PolyStruct1(foo=3, bar=4), PolyStruct2(coo=5) ])
    assert str(s) == "\x01\x04\x01\x02\x01\x04\x03\x04\x02\x03\x05"
