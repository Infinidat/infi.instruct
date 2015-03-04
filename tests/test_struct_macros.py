import unittest
from infi.instruct import ULInt32, VarSizeArray, Struct, ReadPointer

class MacroTestCase(unittest.TestCase):
    def test_var_size_array(self):
        class MyStruct(Struct):
            _fields_ = [ULInt32("counter"), ULInt32("gap"),
                        VarSizeArray("entries", ReadPointer("counter"), ULInt32)]

        string = b"\x03\x00\x00\x00"*2  + b"\x00\x00\x00\x00"*3
        instance = MyStruct.create_from_string(string)
        self.assertEqual(len(instance.entries), 3)

