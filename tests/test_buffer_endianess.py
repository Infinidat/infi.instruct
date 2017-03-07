from infi.instruct.buffer import (Buffer, be_uint_field, le_uint_field, buffer_field,
                                  list_field, str_field)
from infi.instruct.buffer.macros import bytes_ref
import unittest

class TestBufferLE(Buffer):
    three_byte_int = le_uint_field(where=bytes_ref[0:3])

class TestBufferBE(Buffer):
    three_byte_int = be_uint_field(where=bytes_ref[0:3])

class NibbleTestBufferLE(Buffer):
    padding1 = le_uint_field(where=bytes_ref[0].bits[4:8], default=0xf)
    three_byte_int = le_uint_field(where=bytes_ref[0].bits[0:4] + bytes_ref[1:3] + bytes_ref[3].bits[4:8])
    padding2 = le_uint_field(where=bytes_ref[3].bits[0:4], default=0xf)

class NibbleTestBufferBE(Buffer):
    padding1 = be_uint_field(where=bytes_ref[0].bits[4:8], default=0xf)
    three_byte_int = be_uint_field(where=bytes_ref[0].bits[0:4] + bytes_ref[1:3] + bytes_ref[3].bits[4:8])
    padding2 = be_uint_field(where=bytes_ref[3].bits[0:4], default=0xf)

class TestCase(unittest.TestCase):
    def test_little_endian(self):
        tle = TestBufferLE()
        tle.three_byte_int = 0x123456
        self.assertEqual(':'.join(['%02x' % x for x in tle.pack()]), "56:34:12")

        tle2 = TestBufferLE()
        tle2.unpack(tle.pack())
        self.assertEquals(hex(tle2.three_byte_int), '0x123456')

    def test_big_endian(self):
        tbe = TestBufferBE()
        tbe.three_byte_int = 0x123456
        self.assertEqual(':'.join(['%02x' % x for x in tbe.pack()]), "12:34:56")

        tbe2 = TestBufferBE()
        tbe2.unpack(tbe.pack())
        self.assertEquals(hex(tbe2.three_byte_int), '0x123456')
        print hex(tbe2.three_byte_int)


class NibbleTestCase(unittest.TestCase):
    def test_little_endian(self):
        tle = NibbleTestBufferLE()
        tle.three_byte_int = 0x123456
        self.assertEqual(':'.join(['%02x' % x for x in tle.pack()]), "f5:63:41:2f")

        tle2 = NibbleTestBufferLE()
        tle2.unpack(tle.pack())
        self.assertEquals(hex(tle2.three_byte_int), '0x123456')

    def test_big_endian(self):
        tbe = NibbleTestBufferBE()
        tbe.three_byte_int = 0x123456
        self.assertEqual(':'.join(['%02x' % x for x in tbe.pack()]), "f1:23:45:6f")

        tbe2 = NibbleTestBufferBE()
        tbe2.unpack(tbe.pack())
        self.assertEquals(hex(tbe2.three_byte_int), '0x123456')
        print hex(tbe2.three_byte_int)


