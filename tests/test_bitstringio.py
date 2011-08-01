import binascii
from StringIO import StringIO

from infi.instruct.utils.bitstringio import BitStringIO

def test_byte_write():
    io = BitStringIO(1)
    io.write(0x5, 5)
    io.write(0x3, 3)
    assert io.getvalue() == chr(0x05 + (0x03 << 5))

def test_cross_byte_write():
    io = BitStringIO(2)
    io.write(0x3AB, 12)
    io.write(0x02, 4)
    assert io.getvalue() == "\xAB\x23"

def test_cross_byte_read():
    io = BitStringIO("\xAB\x23")
    assert io.read(12) == 0x3AB
    assert io.read(4) == 0x02
