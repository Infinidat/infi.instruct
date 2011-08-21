from infi.instruct.base import ReadOnlyContext
from infi.instruct.numeric import UBInt8Marshal

def test_ubint8():
    assert UBInt8Marshal.create_from_string("a") == ord('a')
    assert UBInt8Marshal.write_to_string(124) == chr(124)

def test_to_repr():
    assert UBInt8Marshal.to_repr(0x0f) == "15"
    assert UBInt8Marshal.to_repr(0x0f, ReadOnlyContext(dict(int_repr_format='%02X'))) == "0F"
