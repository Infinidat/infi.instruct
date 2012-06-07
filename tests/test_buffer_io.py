import random
from bitarray import bitarray
from infi.unittest import TestCase
from infi.instruct.buffer.io_buffer import BitView, BitAwareByteArray

random.seed(0)

class IOBufferTestCase(TestCase):
    def test_getitem__byte(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        self.assertEqual(1, buf[0])
        self.assertEqual(2, buf[1])
        self.assertEqual(1, buf[1.125])
        self.assertEqual(4, buf[2])
        self.assertEqual(2, buf[2.125])
        self.assertEqual(1, buf[2.25])
        self.assertEqual(0, buf[2.375])

        buf = BitAwareByteArray(bytearray((128, 1)), 0, 2)
        self.assertEqual(3, buf[1 - 0.125])

        buf = BitAwareByteArray(bytearray((2, 4)), 0.125, 2)
        self.assertEqual(1, buf[0])
        self.assertEqual(2, buf[1])
        self.assertEqual(1, buf[1.125])

    def test_getitem__range(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4, 128, 1)), 0, 5)
        self.assertEqual([ 1 ], list(buf[0:1]))
        self.assertEqual([ 1, 2 ], list(buf[0:2]))
        self.assertEqual([ 2, 4 ], list(buf[1:3]))
        self.assertEqual([ 2, 4, 128, 1 ], list(buf[1:]))
        self.assertEqual([ 1, 2 ], list(buf[:2]))
        self.assertEqual([ 0, 1 ], list(buf[0.125:2.125]))
        self.assertEqual([ 0, 1 ], list(buf[0.125:2.125]))
        self.assertEqual([ 128, 1], list(buf[-2:]))
        self.assertEqual([ 1 ], list(buf[-10:-4]))
        self.assertEqual([ ], list(buf[-10:-5]))

    def test_setitem__byte(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0:1] = 3
        self.assertEqual([ 3, 2, 4 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0.125:1.125] = 3
        self.assertEqual([ 7, 2, 4 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0.125:1.125] = 0x83
        self.assertEqual([ 7, 3, 4 ], list(buf))

    def test_setitem__bits(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0:0.125] = 0
        self.assertEqual([ 0, 2, 4 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0.125:0.25] = 1
        self.assertEqual([ 3, 2, 4 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[1.125:1.375] = 3
        self.assertEqual([ 1, 6, 4 ], list(buf))

    def test_setitem__insert_into_empty_range(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0.125:0.125] = BitView(bytearray((1,)), 0, 0.125)
        self.assertEqual([ 3, 4, 8, 0 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0:0] = BitView(bytearray((1,)), 0, 0.125)
        self.assertEqual([ 3, 4, 8, 0 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0.25:0.25] = BitView(bytearray(1), 0, 0.125)
        self.assertEqual([ 1, 4, 8, 0 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)), 0, 3)
        buf[0.25:0.25] = BitView(bytearray((1,)), 0, 0.125)
        self.assertEqual([ 5, 4, 8, 0 ], list(buf))

    def test_setitem__smaller_val(self):
        ba = bitarray('1001010111', endian='little')
        bv = BitAwareByteArray(self._bitarray_to_bytes(ba), stop=float(ba.length()) / 8)
        val = bitarray('10', endian='little')
        ba[3:7] = val
        bv[3.0 / 8:7.0 / 8] = BitView(self._bitarray_to_bytes(val), stop=2.0 / 8)
        self.assertEqualBitArrayBitView(ba, bv)

    def test_delitem__bits(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        del buf[0:1]
        self.assertEqual([ 2, 4 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        del buf[1:]
        self.assertEqual([ 1 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        del buf[0:0.125]
        self.assertEqual([ 0, 1, 2 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        del buf[0:1.125]
        self.assertEqual([ 1, 2 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        del buf[0:2.25]
        self.assertEqual([ 1 ], list(buf))

    def test_insert__bytes(self):
        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        buf.insert(3, bytearray((8, 16)))
        self.assertEqual([ 1, 2, 4, 8, 16 ], list(buf))

        buf = BitAwareByteArray(bytearray((1, 2, 4)))
        # 100000000 01000000 00100000
        buf.insert(1.25, bytearray((8, 16)))
        #   100000000 01 00010000 00001000 000000 00100000
        # = 100000000 01000100 00000010 00000000 00100000
        # = 1         34       64       0        4
        self.assertEqual([ 1, 34, 64, 0, 4 ], list(buf))

    def test_extend(self):
        buf = BitAwareByteArray(bytearray((1, 2, 3)))
        buf.extend(bytearray((4, 5)))
        self.assertEqual([ 1, 2, 3, 4, 5 ], list(buf))

    def test_bitview_getitem__single_byte_bitslice(self):
        for i in xrange(0, 256):
            for j in xrange(0, 8):
                bv = BitView(bytearray([ i ]))
                self.assertEqual(list(bv[float(j) / 8:])[0], i >> j)

    def test_bitview_getitem__single_byte_bitslice_with_bits(self):
        for i in xrange(0, 256):
            for j in xrange(0, 8):
                bv = BitView(bytearray([ i ]))
                bv_slice = bv[float(j) / 8:]
                ba = bitarray(endian='little')
                ba.frombytes(chr(i))
                ba_slice = ba[j:]
                self.assertEqualBitArrayBitView(ba_slice, bv_slice)

    def test_bitview__positive_slicing(self):
        for i in xrange(0, 100):
            ba = self._create_random_bit_array()
            bv = BitView(self._bitarray_to_bytes(ba), stop=float(ba.length()) / 8)
            self.assertEqualBitArrayBitView(ba, bv)

            slice_start_in_bits = random.choice(range(0, ba.length() + 10))
            slice_end_in_bits = random.choice(range(slice_start_in_bits, ba.length() + 10))

            ba_slice = ba[slice_start_in_bits:slice_end_in_bits]
            bv_slice = bv[float(slice_start_in_bits) / 8:float(slice_end_in_bits) / 8]
            self.assertEqualBitArrayBitView(ba_slice, bv_slice)

    def test_add(self):
            ba1 = self._create_random_bit_array()
            ba2 = self._create_random_bit_array()
            ba = ba1 + ba2
            bv1 = BitAwareByteArray(self._bitarray_to_bytes(ba1), stop=float(ba1.length()) / 8)
            bv2 = BitAwareByteArray(self._bitarray_to_bytes(ba2), stop=float(ba2.length()) / 8)
            bv = bv1 + bv2
            self.assertEqualBitArrayBitView(ba, bv)

    def test_radd(self):
            ba1 = self._create_random_bit_array()
            ba2 = self._create_random_bit_array()
            ba = ba1 + ba2
            bv1 = BitView(self._bitarray_to_bytes(ba1), stop=float(ba1.length()) / 8)
            bv2 = BitAwareByteArray(self._bitarray_to_bytes(ba2), stop=float(ba2.length()) / 8)
            bv = bv1 + bv2
            self.assertEqualBitArrayBitView(ba, bv)

    def test_iadd(self):
        ba1 = self._create_random_bit_array()
        ba2 = self._create_random_bit_array()
        bv1 = BitAwareByteArray(self._bitarray_to_bytes(ba1), stop=float(ba1.length()) / 8)
        bv2 = BitView(self._bitarray_to_bytes(ba2), stop=float(ba2.length()) / 8)
        ba1 += ba2
        bv1 += bv2
        self.assertEqualBitArrayBitView(ba1, bv1)

    def assertEqualBitArrayBitView(self, ba, bv):
        self.assertEqual(ba.length(), 8 * bv.length())
        ba_bytes = self._bitarray_to_bytes(ba)
        bv_bytes = str(bv)
        self.assertEqual(ba_bytes, bv_bytes)

    def _create_random_bit_array(self):
        length_in_bits = random.randint(0, 8 * 16)
        return bitarray("".join(random.choice(('0', '1')) for i in xrange(length_in_bits)), endian='little')

    def _bitarray_to_bytes(self, b):
        copy = bitarray(b, endian='little')
        copy.fill()
        return bytearray(copy.tobytes())
