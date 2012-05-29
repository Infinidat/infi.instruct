import struct
from infi.unittest import TestCase
from infi.instruct.buffer.range import ByteRangeFactory
from infi.instruct.buffer.serialize import UBInt32Serialize, StringSerialize, ArraySerialize, BufferSerialize
from infi.instruct.buffer.field import FieldReference, NumericFieldReference, AttributeAccessorFactory
from infi.instruct.buffer.buffer import Buffer

bytes_ref = ByteRangeFactory()

def _uint32_field(position, set_value=None):
    before_pack = None
    if set_value:
        before_pack = lambda field, obj: field.value_setter(obj, set_value(obj))
    return NumericFieldReference(None, None,
                                 UBInt32Serialize.serialize, UBInt32Serialize.deserialize, position,
                                 before_pack=before_pack)

def _str_field(position):
    return FieldReference(None, None, StringSerialize.serialize, StringSerialize.deserialize, position)

def _field(position, type):
    return FieldReference(None, None, BufferSerialize.serialize, BufferSerialize.create_deserialize(type), position)

def _uint32_array_field(position):
    return FieldReference(None, None, ArraySerialize.create_serialize(UBInt32Serialize.serialize),
                          ArraySerialize.create_deserialize(UBInt32Serialize.deserialize), position)

from infi.instruct.buffer.reference import Reference, NumericReference
class TotalSize(Reference, NumericReference):
    def value(self, obj):
        return 2

total_size = TotalSize()

class BufferTestCase(TestCase):
    def test_buffer_pack_unpack__varsize_string(self):
        class Foo(Buffer):
            f_int = _uint32_field(bytes_ref[0:4])
            f_str = _str_field(bytes_ref[4:])

            def __init__(self, f_int, f_str):
                self.f_int = f_int
                self.f_str = f_str

        foo = Foo(42, "hello")
        self.assertEqual(struct.pack(">L", foo.f_int) + foo.f_str, foo.pack())

        foo.unpack(struct.pack(">L", 24) + "olleh")
        self.assertEqual(24, foo.f_int)
        self.assertEqual("olleh", foo.f_str)

    def test_buffer_pack_unpack__varsize_string_with_ref(self):
        class Foo(Buffer):
            f_str_len = _uint32_field(bytes_ref[0:4], set_value=lambda self: len(self.f_str))
            f_str = _str_field(bytes_ref[4:4 + f_str_len])

            def __init__(self, f_str):
                self.f_str_len = 0
                self.f_str = f_str

        foo = Foo("hello")
        packed_foo = foo.pack()
        self.assertEqual(len(foo.f_str), foo.f_str_len)
        self.assertEqual(struct.pack(">L", foo.f_str_len) + foo.f_str, packed_foo)

        foo.unpack(struct.pack(">L", len("olleh!")) + "olleh!")
        self.assertEqual(len("olleh!"), foo.f_str_len)
        self.assertEqual("olleh!", foo.f_str)

    def test_buffer_pack_unpack__buffer_with_ref(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(bytes_ref[0:4])
            f_bar_j = _uint32_field(bytes_ref[4:8])

        class Foo(Buffer):
            f_foo_i = _uint32_field(bytes_ref[0:4])
            f_bar = _field(bytes_ref[4:], Bar)

        foo = Foo()
        foo.f_foo_i = 42
        foo.f_bar = Bar()
        foo.f_bar.f_bar_i = 12
        foo.f_bar.f_bar_j = 21
        self.assertEqual(struct.pack(">LLL", foo.f_foo_i, foo.f_bar.f_bar_i, foo.f_bar.f_bar_j), foo.pack())

    def test_buffer_size__static(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(bytes_ref[0:4])
            f_bar_j = _uint32_field(bytes_ref[4:8])
        self.assertEqual(Bar.byte_size, 8)

    def test_buffer_size__dynamic(self):
        class Foo(Buffer):
            f_str_len = _uint32_field(bytes_ref[0:4], set_value=lambda self: len(self.f_str))
            f_str = _str_field(bytes_ref[4:4 + f_str_len])

        self.assertEqual(Foo.byte_size, None)

    def test_buffer_pack_unpack__buffer_with_ref(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(bytes_ref[0:4])
            f_bar_j = _uint32_field(bytes_ref[4:8])

        class Foo(Buffer):
            f_foo_i = _uint32_field(bytes_ref[0:4])
            f_bar = _field(bytes_ref[4:4 + Bar.byte_size], Bar)

        self.assertEqual(Bar.byte_size + 4, Foo.byte_size)

    def test_buffer_calc_byte_size(self):
        class Foo(Buffer):
            f_str_len = _uint32_field(bytes_ref[0:4], set_value=lambda self: len(self.f_str))
            f_str = _str_field(bytes_ref[4:4 + f_str_len])

        foo = Foo()
        foo.f_str = '123'
        self.assertEqual(4 + 3, foo.calc_byte_size())

    def test_buffer_array(self):
        class Foo(Buffer):
            f_int_array = _uint32_array_field(bytes_ref[0:12])

        foo = Foo()
        foo.f_int_array = [ 1, 2, 3 ]
        self.assertEqual(struct.pack(">LLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack(">LLLL", 1, 2, 2, 4))
        self.assertEqual([ 1, 2, 2 ], foo.f_int_array)

    def test_buffer_array_varsize(self):
        class Foo(Buffer):
            f_int_array = _uint32_array_field(bytes_ref[0:])

        foo = Foo()
        foo.f_int_array = [ 1, 2, 3, 4, 5 ]
        self.assertEqual(struct.pack(">LLLLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack(">LLLL", 1, 2, 2, 4))
        self.assertEqual([ 1, 2, 2, 4 ], foo.f_int_array)

    def test_buffer_total_size(self):
        class Foo(Buffer):
            f_int = _uint32_field(bytes_ref[0:4], set_value=lambda self: (total_size.value(self) - 4))
            f_str = _str_field(bytes_ref[4:f_int])

        foo_serialized = struct.pack(">L", 10) + '0123456789'
        foo = Foo()
        foo.unpack(foo_serialized)
        self.assertEqual(10, foo.f_int)
        self.assertEqual('0123456789', foo.f_str)

        foo = Foo()
        foo.f_str = '01234'
        self.assertEqual(struct.pack('>L', 5) + '01234', foo.pack())
