import struct
from bitarray import bitarray
from infi.unittest import TestCase
from infi.instruct.buffer.buffer import Buffer, InstructBufferError
from infi.instruct.buffer.macros import int_field, float_field, str_field, buffer_field, list_field
from infi.instruct.buffer.macros import bytes_ref, total_size, n_uint32, be_int_field
from infi.exceptools import *


def junk_generator(size):
    import string
    import random
    chars = string.letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for x in range(size))


class BufferTestCase(TestCase):
    def test_buffer_pack_unpack__int(self):
        class Foo(Buffer):
            f_int = int_field(where=bytes_ref[0:4])
        foo = Foo()
        foo.f_int = 42
        self.assertEqual(struct.pack("=l", foo.f_int), foo.pack())
        foo.unpack("\xFF\x00\x00\x00")
        self.assertEqual(255, foo.f_int)

    def test_buffer_pack_unpack__float(self):
        class Foo(Buffer):
            f_float = float_field(where=bytes_ref[0:4])
        foo = Foo()
        foo.f_float = 42.42
        self.assertEqual(struct.pack("=f", foo.f_float), foo.pack())
        foo.unpack(struct.pack("=f", 64))
        self.assertEqual(64, foo.f_float)

    def test_buffer_pack_unpack__varsize_string(self):
        class Foo(Buffer):
            f_int = int_field(where=bytes_ref[0:4])
            f_str = str_field(where=bytes_ref[4:])

            def __init__(self, f_int, f_str):
                self.f_int = f_int
                self.f_str = f_str

        foo = Foo(42, "hello")
        self.assertEqual(struct.pack("=l", foo.f_int) + foo.f_str, foo.pack())

        foo.unpack(struct.pack("=l", 24) + "olleh")
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
            f_int = int_field(sign='unsigned',
                              where=(bytes_ref[7].bits[0:4] +
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
            f_int = int_field(sign='unsigned',
                              where=(bytes_ref[0:2].bits[4:12] + bytes_ref[2:4].bits[4:12] +
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

    def test_buffer_bits__partial(self):
        class Foo(Buffer):
            f_int = int_field(where=(bytes_ref[0] + bytes_ref[1].bits[0:4]))

        class Foo2(Buffer):
            f_int = int_field(where=(bytes_ref[1].bits[0:4] + bytes_ref[0]))

        self.assertEqual(1.5, Foo.byte_size)
        foo = Foo()
        foo.f_int = 0xcff
        self.assertEquals(foo.pack(), b"\xff\x0c")

        foo = Foo2()
        foo.f_int = 0xcff
        self.assertEquals(foo.pack(), b"\xcf\x0f")

    def test_buffer_bits__add(self):
        class CoolingElementInfo(Buffer):
            byte_size = 3
            # for real fan speed the fan speed value should be multiplied by a factor of 10
            fan_speed = int_field(where=(bytes_ref[0].bits[0:3] + bytes_ref[1]))
            ident = be_int_field(where=bytes_ref[0].bits[7])
            speed_code = be_int_field(where=bytes_ref[2].bits[0:3])
            off = be_int_field(where=bytes_ref[2].bits[4])
            reqstd_on = be_int_field(where=bytes_ref[2].bits[5])
            fail = be_int_field(where=bytes_ref[2].bits[6])
            hot_swap = be_int_field(where=bytes_ref[2].bits[7])

        f = CoolingElementInfo()
        f.unpack("\x03\x8E\x25")
        self.assertTrue(f.fan_speed < (1 << 12), "fan_speed is {0}, bit length {1}".format(f.fan_speed, f.fan_speed.bit_length()))

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

    def test_buffer_pack_unpack__buffer_with_ref2(self):
        class Bar(Buffer):
            f_bar_i = int_field(where=bytes_ref[0:4])
            f_bar_j = int_field(where=bytes_ref[4:8])

        class Foo(Buffer):
            f_foo_i = int_field(where=bytes_ref[0:4])
            f_bar = buffer_field(where=bytes_ref[4:], type=Bar)

        foo = Foo()
        foo.f_foo_i = 42
        foo.f_bar = Bar()
        foo.f_bar.f_bar_i = 12
        foo.f_bar.f_bar_j = 21
        self.assertEqual(struct.pack("=LLL", foo.f_foo_i, foo.f_bar.f_bar_i, foo.f_bar.f_bar_j), foo.pack())

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
            f_bar = buffer_field(where=bytes_ref[4:4 + Bar.byte_size], type=Bar)

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
            f_int_array = list_field(where=bytes_ref[0:12], type=n_uint32)

        foo = Foo()
        foo.f_int_array = [1, 2, 3]
        self.assertEqual(struct.pack("=LLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack("=LLLL", 1, 2, 2, 4))
        self.assertEqual([1, 2, 2], foo.f_int_array)

    def test_buffer_pack_unpack__fixed_size_list2(self):
        class Foo(Buffer):
            f_int_array = list_field(where=bytes_ref[0:], type=n_uint32)

        foo = Foo()
        foo.f_int_array = [1, 2, 3, 4, 5]
        self.assertEqual(struct.pack("=LLLLL", *foo.f_int_array), foo.pack())
        foo.f_int_array = None
        foo.unpack(struct.pack("=LLLL", 1, 2, 2, 4))
        self.assertEqual([1, 2, 2, 4], foo.f_int_array)

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
        self.assertEquals("test_buffer_buffer.Foo(f_int=11, f_str='hello world')", repr(foo))

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

    def test_buffer_bits(self):
        class Foo(Buffer):
            f_a = int_field(where=bytes_ref[0].bits[0:4])
            f_b = int_field(where=bytes_ref[0].bits[4:8])

        self.assertEquals(1, Foo.byte_size)
        foo = Foo()
        foo.f_a = 3
        foo.f_b = 8
        self.assertEqual("\x83", foo.pack())

        foo = Foo()
        foo.unpack("\x12")
        self.assertEqual(foo.f_a, 2)
        self.assertEqual(foo.f_b, 1)

    def test_buffer_str_justify(self):
        class Foo(Buffer):
            f_a = str_field(where=bytes_ref[0:8], justify='right', padding=' ')

        foo = Foo()
        foo.f_a = '123'
        self.assertEquals("     123", foo.pack())

        foo.unpack(" 1234567")
        self.assertEquals("1234567", foo.f_a)

    def test_buffer_selector(self):
        class Bar(Buffer):
            f_a = int_field(where=bytes_ref[0:4])

        class Bar2(Bar):
            f_b = int_field(where=bytes_ref[4:8])

        class Foo(Buffer):
            def _choose_bar(self, buffer, **kwargs):
                return Bar if self.f_select == 0 else Bar2

            f_select = int_field(where=bytes_ref[0:4])
            f_obj = buffer_field(where=bytes_ref[4:], type=Bar, unpack_selector=_choose_bar, unpack_after=f_select)

        foo = Foo()
        foo.f_select = 0
        foo.f_obj = Bar()
        foo.f_obj.f_a = 42
        self.assertEquals(struct.pack("=LL", 0, 42), foo.pack())

        foo.f_select = 1
        foo.f_obj = Bar2()
        foo.f_obj.f_a = 42
        foo.f_obj.f_b = 24
        self.assertEquals(struct.pack("=LLL", 1, 42, 24), foo.pack())

        foo = Foo()
        foo.unpack(struct.pack("=LLL", 1, 13, 31))
        self.assertEquals(1, foo.f_select)
        self.assertEquals(13, foo.f_obj.f_a)
        self.assertEquals(31, foo.f_obj.f_b)

    def test_single_bits(self):
        # ses3r05: 7.3.25
        class SasExpanderElementInfo(Buffer):
            byte_size = 3
            fail = be_int_field(where=bytes_ref[0].bits[6])
            ident = be_int_field(where=bytes_ref[0].bits[7])

        f = SasExpanderElementInfo()
        f.unpack("\x00\x00\x00")
        self.assertEquals(f.pack(), "\x00\x00\x00")

    def test_buffer_list_selector(self):
        class Bar(Buffer):
            f_a = int_field(where=bytes_ref[0:4])

            def __init__(self, f_a=0):
                self.f_a = f_a

            def __eq__(self, other):
                return self.f_a == other.f_a

        class Bar2(Bar):
            f_b = int_field(where=bytes_ref[4:8])

            def __init__(self, f_a=0, f_b=0):
                super(Bar2, self).__init__(f_a)
                self.f_b = f_b

            def __eq__(self, other):
                return self.f_a == other.f_a and self.f_b == other.f_b

        class Foo(Buffer):
            def _choose_bar(self, buffer, **kwargs):
                return Bar if self.f_select == 0 else Bar2

            f_select = int_field(where=bytes_ref[0:4])
            f_list = list_field(where=bytes_ref[4:], type=Bar,
                                unpack_selector=_choose_bar,
                                unpack_after=f_select)

        foo = Foo()
        foo.f_select = 0
        foo.f_list = [Bar(1), Bar(2), Bar(3)]
        self.assertEquals(struct.pack("=LLLL", 0, 1, 2, 3), foo.pack())

        foo.f_select = 1
        foo.f_list = [Bar2(1, 2), Bar2(3, 4), Bar2(5, 6)]
        self.assertEquals(struct.pack("=LLLLLLL", 1, 1, 2, 3, 4, 5, 6), foo.pack())

        foo = Foo()
        foo.unpack(struct.pack("=LLL", 0, 13, 31))
        self.assertEquals(0, foo.f_select)
        self.assertEquals([Bar(13), Bar(31)], foo.f_list)

        foo = Foo()
        foo.unpack(struct.pack("=LLLLLLL", 1, 13, 31, 12, 21, 45, 54))
        self.assertEquals(1, foo.f_select)
        self.assertEquals([Bar2(13, 31), Bar2(12, 21), Bar2(45, 54)], foo.f_list)

    def test_buffer_init(self):
        class Foo(Buffer):
            f_a = int_field(where=bytes_ref[0:4])
        f = Foo(f_a=1)
        self.assertEquals(f.pack(), struct.pack("=l", 1))

    def test_buffer_default(self):
        class Foo(Buffer):
            f_a = int_field(where=bytes_ref[0:4], default=42)

        f = Foo()
        self.assertEquals(f.f_a, 42)

        f = Foo(f_a=43)
        self.assertEquals(f.f_a, 43)

        f = Foo()
        f.f_a = 44
        self.assertEquals(f.f_a, 44)

    def test_empty_range(self):
        class Foo(Buffer):
            l = be_int_field(where=bytes_ref[2:4])
            s = str_field(where_when_pack=bytes_ref[4:], where_when_unpack=bytes_ref[4:l + 4])

        f = Foo()
        f.l = 0
        f.s = ""
        self.assertEquals(f.pack(), "\x00\x00\x00\x00")
        f.unpack("\x00\x00\x00\x00")

    def test_set_buffer_on_pack(self):
        class Foo(Buffer):
            l = be_int_field(where=bytes_ref[0])

        class Bar(Buffer):
            f = buffer_field(type=Foo, where=bytes_ref[0], set_before_pack=Foo(l=1))

        b = Bar()
        b.pack()

    def test_buffer_with_junk(self):
        class Foo(Buffer):
            l = be_int_field(where=bytes_ref[0:2])
            s = str_field(where_when_pack=bytes_ref[2:], where_when_unpack=bytes_ref[2:l + 4])

        f = Foo()
        f.s = "hello world"
        f.l = len(f.s)
        self.assertEquals(f.pack(), "\x00\x0bhello world")

        b = "\x00\x0bhello world" + junk_generator(0x10000)
        f.unpack(b)
