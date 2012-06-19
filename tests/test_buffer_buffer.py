import struct
from bitarray import bitarray
from infi.unittest import TestCase
from infi.instruct.buffer.reference import CyclicReferenceError
from infi.instruct.buffer.buffer import Buffer, InstructBufferError
from infi.instruct.buffer.macros import int_field, float_field, str_field, field, list_field
from infi.instruct.buffer.macros import bytes_ref, total_size, int32
from infi.exceptools import *

class BufferTestCase(TestCase):
    def test_buffer_pack_unpack__varsize_string(self):
        class Foo(Buffer):
            f_int = int_field(where=bytes_ref[0:4])
            f_str = str_field(where=bytes_ref[4:])

            def __init__(self, f_int, f_str):
                self.f_int = f_int
                self.f_str = f_str

        foo = Foo(42, "hello")
        self.assertEqual(struct.pack("=L", foo.f_int) + foo.f_str, foo.pack())

        foo.unpack(struct.pack("=L", 24) + "olleh")
        self.assertEqual(24, foo.f_int)
        self.assertEqual("olleh", foo.f_str)

    def test_buffer_pack_unpack__varsize(self):
        class Foo(Buffer):
            f_int = int_field(where=bytes_ref[0:4], set_before_pack=total_size - 4)
            f_str = str_field(where_when_pack=bytes_ref[4:], where_when_unpack=bytes_ref[4:4 + f_int])

        foo = Foo()
        foo.f_int = 0
        foo.f_str = 'hello world'
        self.assertEqual(struct.pack("=L", len(foo.f_str)) + 'hello world', foo.pack())

    def test_buffer_bits__simple(self):
        class Foo(Buffer):
            f_int = int_field(where=(bytes_ref[7].bits[0:4] +
                                     bytes_ref[6].bits[0:4] +
                                     bytes_ref[5].bits[0:4] +
                                     bytes_ref[4].bits[0:4] +
                                     bytes_ref[3].bits[0:4] +
                                     bytes_ref[2].bits[0:4] +
                                     bytes_ref[1].bits[0:4] +
                                     bytes_ref[0].bits[0:4]))

        self.assertEqual(7.5, Foo.byte_size)
        for n in (0x12345678, 0x87654321, 0, 1, 0x10000000, 0xFF000000):
            foo = Foo()
            foo.f_int = n
            packed_value = foo.pack()
            self.assertEqual(8, len(packed_value))
            packed_result = bytearray(8)
            for i in xrange(8):
                packed_result[7 - i] = (foo.f_int >> (i * 4)) & 0x0F
            self.assertEqual(packed_result, packed_value)
            foo = Foo()
            foo.unpack(packed_result)
            self.assertEqual(foo.f_int, n)

    def test_buffer_bits__complex(self):
        class Foo(Buffer):
            f_int = int_field(where=(bytes_ref[0:2].bits[4:12] + bytes_ref[2:4].bits[4:12] +
                                     bytes_ref[4:6].bits[4:12] + bytes_ref[6:8].bits[4:12]))

        self.assertEqual(7.5, Foo.byte_size)
        for n in (0xFF000000, 0x12345678, 0x87654321, 0, 1, 0x10000000, 0xFF000000):
            foo = Foo()
            foo.f_int = n
            packed_value = foo.pack()
            self.assertEqual(8, len(packed_value))

            ba = bitarray('0' * (8 * 8), endian='little')
            int_pack = struct.pack("<L", foo.f_int)
            for i in xrange(4):
                b = bitarray(endian='little')
                b.frombytes(int_pack[i])
                ba[i * 2 * 8 + 4:i * 2 * 8 + 4 + 8] = b
            self.assertEqual(ba.tobytes(), packed_value)

    def test_buffer_size__static(self):
        class Bar(Buffer):
            f_bar_i = int_field(where=bytes_ref[0:4])
            f_bar_j = int_field(where=bytes_ref[4:8])
        self.assertEqual(8, Bar.byte_size)

    def test_buffer_pack_unpack__varsize_string_with_ref(self):
        class Foo(Buffer):
            f_str_len = int_field(where=bytes_ref[0:4], set_before_pack=lambda self: len(self.f_str))
            f_str = str_field(where=bytes_ref[4:4 + f_str_len])

            def __init__(self, f_str):
                self.f_str_len = 0
                self.f_str = f_str

        foo = Foo("hello")
        packed_foo = foo.pack()
        self.assertEqual(len(foo.f_str), foo.f_str_len)
        self.assertEqual(struct.pack("=L", foo.f_str_len) + foo.f_str, packed_foo)

        foo.unpack(struct.pack("=L", len("olleh!")) + "olleh!")
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

    def test_buffer_size__dynamic(self):
        class Foo(Buffer):
            f_str_len = int_field(where=bytes_ref[0:4], set_before_pack=lambda self: len(self.f_str))
            f_str = str_field(where=bytes_ref[4:4 + f_str_len])

        self.assertEqual(Foo.byte_size, None)

    def test_buffer_pack_unpack__buffer_with_ref(self):
        class Bar(Buffer):
            f_bar_i = int_field(where=bytes_ref[0:4])
            f_bar_j = int_field(where=bytes_ref[4:8])

        class Foo(Buffer):
            f_foo_i = int_field(where=bytes_ref[0:4])
            f_bar = field(where=bytes_ref[4:4 + Bar.byte_size], type=Bar)

        self.assertEqual(Bar.byte_size + 4, Foo.byte_size)

    def test_buffer_calc_byte_size(self):
        class Foo(Buffer):
            f_str_len = int_field(where=bytes_ref[0:4], set_before_pack=lambda self: len(self.f_str))
            f_str = str_field(where=bytes_ref[4:4 + f_str_len])

        foo = Foo()
        foo.f_str = '123'
        self.assertEqual(4 + 3, foo.calc_byte_size())

    def test_buffer_pack_unpack__fixed_size_list(self):
        class Foo(Buffer):
            f_int_array = list_field(where=bytes_ref[0:12], type=int32("unsigned", "native"))

        foo = Foo()
        foo.f_int_array = [ 1, 2, 3 ]
        self.assertEqual(struct.pack("=LLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack("=LLLL", 1, 2, 2, 4))
        self.assertEqual([ 1, 2, 2 ], foo.f_int_array)

    def test_buffer_pack_unpack__fixed_size_list2(self):
        class Foo(Buffer):
            f_int_array = list_field(where=bytes_ref[0:], type=int32("unsigned", "native"))

        foo = Foo()
        foo.f_int_array = [ 1, 2, 3, 4, 5 ]
        self.assertEqual(struct.pack("=LLLLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack("=LLLL", 1, 2, 2, 4))
        self.assertEqual([ 1, 2, 2, 4 ], foo.f_int_array)

    def test_buffer_total_size(self):
        class Foo(Buffer):
            f_int = int_field(where=bytes_ref[0:4], set_before_pack=total_size - 4)
            f_str = str_field(where_when_pack=bytes_ref[4:],
                              where_when_unpack=bytes_ref[4:4 + f_int])

        foo_serialized = struct.pack("=L", 10) + '0123456789'
        self.assertEqual(len(foo_serialized), 4 + 10)
        foo = Foo()
        foo.unpack(foo_serialized)
        self.assertEqual(10, foo.f_int)
        self.assertEqual('0123456789', foo.f_str)

        foo = Foo()
        foo.f_str = '01234'
        self.assertEqual(struct.pack('=L', 5) + '01234', foo.pack())

    def test_buffer_cyclic_reference(self):
        with self.assertRaises(InstructBufferError):
            class Foo(Buffer):
                f_int = int_field(where=bytes_ref[0:4], set_before_pack=total_size)
                f_str = str_field(where=bytes_ref[4:f_int])

            f = Foo()
            f.f_str = 'hello'
            f.pack()

    def test_buffer_repr(self):
        class Foo(Buffer):
            f_int = int_field(where=bytes_ref[0:4], set_before_pack=total_size - 4)
            f_str = str_field(where_when_pack=bytes_ref[4:],
                              where_when_unpack=bytes_ref[4:4 + f_int])
        foo = Foo()
        foo.f_str = 'hello world'
        foo.pack()
        print(repr(foo))

    def test_buffer_self_call(self):
        class Bar(Buffer):
            def _do_something(self):
                assert self.f_bar_j == 5
                self.f_bar_i = 10
                return self.f_bar_i

            f_bar_i = int_field(where=bytes_ref[0:4], set_before_pack=_do_something)
            f_bar_j = int_field(where=bytes_ref[4:8])

        b = Bar()
        b.f_bar_i = 1
        b.f_bar_j = 5

        self.assertEqual(struct.pack("=LL", 10, 5), b.pack())
        self.assertEqual(10, b.f_bar_i)
