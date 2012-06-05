import struct
from infi.unittest import TestCase
from infi.instruct.buffer.reference import CyclicReferenceError
from infi.instruct.buffer.range import RangeFactory
from infi.instruct.buffer.serialize import UBInt32PackReference, UBInt32UnpackReference
from infi.instruct.buffer.serialize import StringPackReference, StringUnpackReference
from infi.instruct.buffer.serialize import BufferPackReference, BufferUnpackReference
from infi.instruct.buffer.serialize import ListPackReference, FixedSizeListUnpackReference
from infi.instruct.buffer.buffer import Buffer, TotalSizeReference, FieldReferenceBuilder, InstructBufferError

bytes_ref = RangeFactory()
total_size = TotalSizeReference()

def _create_builder_from_params(position=None, pack_position=None, unpack_position=None,
                                pack_value=None, unpack_value=None, **kwargs):
    builder = FieldReferenceBuilder()
    builder.set_position(position)
    builder.set_pack_position(pack_position)
    builder.set_unpack_position(unpack_position)
    builder.set_pack_value(pack_value)
    builder.set_unpack_value(unpack_value)
    return builder

def _uint32_field(*args, **kwargs):
    builder = _create_builder_from_params(**kwargs)
    builder.set_numeric(True)
    builder.set_pack_class(UBInt32PackReference)
    builder.set_unpack_class(UBInt32UnpackReference)
    return builder.create()

def _str_field(*args, **kwargs):
    builder = _create_builder_from_params(**kwargs)
    builder.set_pack_class(StringPackReference)
    builder.set_unpack_class(StringUnpackReference)
    return builder.create()

def _buffer_field(*args, **kwargs):
    builder = _create_builder_from_params(**kwargs)
    builder.set_pack_class(BufferPackReference.create_factory(kwargs["type"]))
    # TODO: requires position based on fixed size - if the struct is not a fixed size, we require position...
    builder.set_unpack_class(BufferPackReference.create_factory(kwargs["type"]))
    return builder.create()

def _uint32_list_field(position):
    builder = _create_builder_from_params(position=position)
    builder.set_pack_class(ListPackReference.create_factory(UBInt32PackReference))
    builder.set_unpack_class(FixedSizeListUnpackReference.create_factory(UBInt32UnpackReference,
                                                                         UBInt32UnpackReference.byte_size))
    return builder.create()

class BufferTestCase(TestCase):
    def test_buffer_pack_unpack__varsize_string(self):
        class Foo(Buffer):
            f_int = _uint32_field(position=bytes_ref[0:4])
            f_str = _str_field(position=bytes_ref[4:])

            def __init__(self, f_int, f_str):
                self.f_int = f_int
                self.f_str = f_str

        foo = Foo(42, "hello")
        self.assertEqual(struct.pack(">L", foo.f_int) + foo.f_str, foo.pack())

        foo.unpack(struct.pack(">L", 24) + "olleh")
        self.assertEqual(24, foo.f_int)
        self.assertEqual("olleh", foo.f_str)

    def test_buffer_pack_unpack__varsize(self):
        class Foo(Buffer):
            f_int = _uint32_field(position=bytes_ref[0:4], pack_value=total_size - 4)
            f_str = _str_field(pack_position=bytes_ref[4:],
                               unpack_position=bytes_ref[4:4 + f_int])

        foo = Foo()
        foo.f_int = 0
        foo.f_str = 'hello world'
        self.assertEqual(struct.pack(">L", len(foo.f_str)) + 'hello world', foo.pack())


    def test_buffer_size__static(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(position=bytes_ref[0:4])
            f_bar_j = _uint32_field(position=bytes_ref[4:8])
        self.assertEqual(8, Bar.byte_size)

    def test_buffer_size__dynamic(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(position=bytes_ref[0:4])
            f_bar_j = _str_field(position=bytes_ref[4:])
        self.assertEqual(None, Bar.byte_size)

    def test_buffer_pack_unpack__varsize_string_with_ref(self):
        class Foo(Buffer):
            f_str_len = _uint32_field(position=bytes_ref[0:4], pack_value=lambda self: len(self.f_str))
            f_str = _str_field(position=bytes_ref[4:4 + f_str_len])

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
            f_bar_i = _uint32_field(position=bytes_ref[0:4])
            f_bar_j = _uint32_field(position=bytes_ref[4:8])

        class Foo(Buffer):
            f_foo_i = _uint32_field(position=bytes_ref[0:4])
            f_bar = _buffer_field(position=bytes_ref[4:], type=Bar)

        foo = Foo()
        foo.f_foo_i = 42
        foo.f_bar = Bar()
        foo.f_bar.f_bar_i = 12
        foo.f_bar.f_bar_j = 21
        self.assertEqual(struct.pack(">LLL", foo.f_foo_i, foo.f_bar.f_bar_i, foo.f_bar.f_bar_j), foo.pack())

    def test_buffer_size__static(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(position=bytes_ref[0:4])
            f_bar_j = _uint32_field(position=bytes_ref[4:8])
        self.assertEqual(Bar.byte_size, 8)

    def test_buffer_size__dynamic(self):
        class Foo(Buffer):
            f_str_len = _uint32_field(position=bytes_ref[0:4], pack_value=lambda self: len(self.f_str))
            f_str = _str_field(position=bytes_ref[4:4 + f_str_len])

        self.assertEqual(Foo.byte_size, None)

    def test_buffer_pack_unpack__buffer_with_ref(self):
        class Bar(Buffer):
            f_bar_i = _uint32_field(position=bytes_ref[0:4])
            f_bar_j = _uint32_field(position=bytes_ref[4:8])

        class Foo(Buffer):
            f_foo_i = _uint32_field(position=bytes_ref[0:4])
            f_bar = _buffer_field(position=bytes_ref[4:4 + Bar.byte_size], type=Bar)

        self.assertEqual(Bar.byte_size + 4, Foo.byte_size)

    def test_buffer_calc_byte_size(self):
        class Foo(Buffer):
            f_str_len = _uint32_field(position=bytes_ref[0:4], pack_value=lambda self: len(self.f_str))
            f_str = _str_field(position=bytes_ref[4:4 + f_str_len])

        foo = Foo()
        foo.f_str = '123'
        self.assertEqual(4 + 3, foo.calc_byte_size())

    def test_buffer_pack_unpack__fixed_size_list(self):
        class Foo(Buffer):
            f_int_array = _uint32_list_field(position=bytes_ref[0:12])

        foo = Foo()
        foo.f_int_array = [ 1, 2, 3 ]
        self.assertEqual(struct.pack(">LLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack(">LLLL", 1, 2, 2, 4))
        self.assertEqual([ 1, 2, 2 ], foo.f_int_array)

    def test_buffer_pack_unpack__fixed_size_list2(self):
        class Foo(Buffer):
            f_int_array = _uint32_list_field(bytes_ref[0:])

        foo = Foo()
        foo.f_int_array = [ 1, 2, 3, 4, 5 ]
        self.assertEqual(struct.pack(">LLLLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack(">LLLL", 1, 2, 2, 4))
        self.assertEqual([ 1, 2, 2, 4 ], foo.f_int_array)

    def test_buffer_total_size(self):
        class Foo(Buffer):
            f_int = _uint32_field(position=bytes_ref[0:4], pack_value=total_size - 4)
            f_str = _str_field(pack_position=bytes_ref[4:],
                               unpack_position=bytes_ref[4:4 + f_int])

        foo_serialized = struct.pack(">L", 10) + '0123456789'
        foo = Foo()
        foo.unpack(foo_serialized)
        self.assertEqual(10, foo.f_int)
        self.assertEqual('0123456789', foo.f_str)

        foo = Foo()
        foo.f_str = '01234'
        self.assertEqual(struct.pack('>L', 5) + '01234', foo.pack())

    def test_buffer_cyclic_reference(self):
        with self.assertRaises(InstructBufferError):
            class Foo(Buffer):
                f_int = _uint32_field(position=bytes_ref[0:4], pack_value=total_size)
                f_str = _str_field(position=bytes_ref[4:f_int])

    def test_buffer_repr(self):
        class Foo(Buffer):
            f_int = _uint32_field(position=bytes_ref[0:4], pack_value=total_size - 4)
            f_str = _str_field(pack_position=bytes_ref[4:],
                               unpack_position=bytes_ref[4:4 + f_int])
        foo = Foo()
        foo.f_str = 'hello world'
        foo.pack()
        print(repr(foo))
