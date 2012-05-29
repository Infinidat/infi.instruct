import struct
from infi.unittest import TestCase
from infi.instruct.buffer.field import Field, AttributeAccessorFactory, FieldReference, NumericFieldReference
from infi.instruct.buffer.serialize import UBInt32Serialize, StringSerialize
from infi.instruct.buffer.io_buffer import InputBuffer, OutputBuffer

class FieldTestCase(TestCase):
    class MyClass(object):
        def __init__(self, f_int, f_str):
            self.f_int = f_int
            self.f_str = f_str

    def test_field_pack(self):
        f_int = self._create_field('f_int', UBInt32Serialize, [ slice(0, 4, 1) ])
        f_str = self._create_field('f_str', StringSerialize, [ slice(4, None, 1) ])
        out = OutputBuffer()

        obj = FieldTestCase.MyClass(42, "kawabonga")
        f_int.pack(obj, out)
        f_str.pack(obj, out)
        self.assertEquals(struct.pack(">L", obj.f_int) +  obj.f_str, out.get())

    def test_field_unpack(self):
        f_int = self._create_field('f_int', UBInt32Serialize, [ slice(0, 4, 1) ])
        f_str = self._create_field('f_str', StringSerialize, [ slice(4, None, 1) ])
        input = InputBuffer(struct.pack(">L", 42) + "kawabonga")

        obj = FieldTestCase.MyClass(0, "")
        f_int.unpack(obj, input)
        f_str.unpack(obj, input)
        self.assertEquals(42, obj.f_int)
        self.assertEquals("kawabonga", obj.f_str)

    def test_numeric_field_reference(self):
        f_int = self._create_field_reference('f_int', UBInt32Serialize, [ slice(0, 4, 1) ], cls=NumericFieldReference)
        self.assertEquals(10, f_int.value(FieldTestCase.MyClass(10, '')))

    def test_numeric_field_reference__add_expr(self):
        f_int = self._create_field_reference('f_int', UBInt32Serialize, [ slice(0, 4, 1) ], cls=NumericFieldReference)
        self.assertEquals(14, (f_int + 4).value(FieldTestCase.MyClass(10, '')))

    def _create_field(self, name, serialize_class, position):
        return Field(AttributeAccessorFactory.create_getter(name), AttributeAccessorFactory.create_setter(name),
                     serialize_class.serialize, serialize_class.deserialize, position)

    def _create_field_reference(self, name, serialize_class, position, cls=FieldReference):
        return cls(AttributeAccessorFactory.create_getter(name), AttributeAccessorFactory.create_setter(name),
                   serialize_class.serialize, serialize_class.deserialize, position)
