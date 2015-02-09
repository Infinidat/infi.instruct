from infi.instruct.base import ReadOnlyContext
from infi.instruct.numeric import UBInt8Marshal
from infi.instruct._compat import PY2

def test_ubint8():
    assert UBInt8Marshal.create_from_string(b"a") == ord('a')
    expected_result = chr(124) if PY2 else bytes([124])
    assert UBInt8Marshal.write_to_string(124) == expected_result

def test_to_repr():
    assert UBInt8Marshal.to_repr(0x0f) == "15"
    assert UBInt8Marshal.to_repr(0x0f, ReadOnlyContext(dict(int_repr_format='%02X'))) == "0F"
