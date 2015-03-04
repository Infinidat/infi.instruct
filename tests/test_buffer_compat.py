import unittest
from infi.instruct.buffer.compat import buffer_to_struct_adapter
from infi.instruct.buffer import Buffer, int_field, bytes_ref


class CompatTestCase(unittest.TestCase):
    def test_buffer_to_struct_adapter__create_from_string(self):
        class MyBuffer(Buffer):
            a = int_field(where=bytes_ref[0:4])
            b = int_field(where=bytes_ref[4:8])

        s = buffer_to_struct_adapter(MyBuffer)
        b = s.create_from_string(b"\xff\x00\x00\x00\xfe\x00\x00\x00")
        self.assertEquals(b.a, 0xff)
        self.assertEquals(b.b, 0xfe)
