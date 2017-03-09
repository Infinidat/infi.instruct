import random
from bitarray import bitarray
from infi.instruct._compat import range, PY2
from infi.unittest import TestCase
from infi.instruct.buffer.io_buffer import BitView, BitAwareByteArray

random.seed(0)


class IOBufferTestCase(TestCase):
    def test_getitem__byte(self):
        buf = BitAwareByteArray(b"\x01\x02\x04")
        self.assertEqual(1, buf[0])
        self.assertEqual(2, buf[1])
        self.assertEqual(1, buf[1.125])
        self.assertEqual(4, buf[2])
        self.assertEqual(2, buf[2.125])
        self.assertEqual(1, buf[2.25])
        self.assertEqual(0, buf[2.375])

        buf = BitAwareByteArray(b"\x80\x01")
        self.assertEqual(3, buf[1 - 0.125])

        buf = BitAwareByteArray(b"\x02\x04", 0.125, 2)
        self.assertEqual(1, buf[0])
        self.assertEqual(2, buf[1])
        self.assertEqual(1, buf[1.125])

    def test_getitem__range(self):
        buf = BitAwareByteArray(b"\x01\x02\x04\x80\x01")
        self.assertEqual([1], list(buf[0:1]))
        self.assertEqual([1, 2], list(buf[0:2]))
        self.assertEqual([2, 4], list(buf[1:3]))
        self.assertEqual([2, 4, 128, 1], list(buf[1:]))
        self.assertEqual([1, 2], list(buf[:2]))
        self.assertEqual([0, 1], list(buf[0.125:2.125]))
        self.assertEqual([0, 1], list(buf[0.125:2.125]))
        self.assertEqual([128, 1], list(buf[-2:]))
        self.assertEqual([1], list(buf[-10:-4]))
        self.assertEqual([], list(buf[-10:-5]))

    def test_setitem__byte(self):
        buf = BitAwareByteArray(b"\x01\x02\x04", 0, 3)
        buf[0:1] = b"\x03"
        self.assertEqual([3, 2, 4], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04", 0, 3)
        buf[0.125:1.125] = b"\x03"
        self.assertEqual([7, 2, 4], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04", 0, 3)
        buf[0.125:1.125] = b"\x83"
        self.assertEqual([7, 3, 4], list(buf))

    def test_setitem__insert_into_empty_range(self):
        buf = BitAwareByteArray(b"\x01\x02\x04")
        buf[0.125:0.125] = BitView(b"\x01", 0, 0.125)
        self.assertEqual([3, 4, 8, 0], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        buf[0:0] = BitView(b"\x01", 0, 0.125)
        self.assertEqual([3, 4, 8, 0], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        buf[0.25:0.25] = BitView(b"\x01", 0, 0.125)
        self.assertEqual([5, 4, 8, 0], list(buf))

    def test_setitem__smaller_val(self):
        ba = bitarray('1001010111', endian='little')
        bv = BitAwareByteArray(self._bitarray_to_bytes(ba), stop=float(ba.length()) / 8)
        val = bitarray('10', endian='little')
        ba[3:7] = val
        bv[3.0 / 8:7.0 / 8] = BitView(self._bitarray_to_bytes(val), stop=2.0 / 8)
        self.assertEqualBitArrayBitView(ba, bv)

    def test_delitem__bits(self):
        buf = BitAwareByteArray(b"\x01\x02\x04")
        del buf[0:1]
        self.assertEqual([2, 4], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        del buf[1:]
        self.assertEqual([1], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        del buf[0:0.125]
        self.assertEqual([0, 1, 2], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        del buf[0:1.125]
        self.assertEqual([1, 2], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        del buf[0:2.25]
        self.assertEqual([1], list(buf))

    def test_insert__bytes(self):
        buf = BitAwareByteArray(b"\x01\x02\x04")
        buf.insert(3, "\x08\x10")
        self.assertEqual([1, 2, 4, 8, 16], list(buf))

        buf = BitAwareByteArray(b"\x01\x02\x04")
        # 100000000 01000000 00100000
        buf.insert(1.25, b"\x08\x10")
        #   100000000 01 00010000 00001000 000000 00100000
        # = 100000000 01000100 00000010 00000000 00100000
        # = 1         34       64       0        4
        self.assertEqual([1, 34, 64, 0, 4], list(buf))

    def test_extend(self):
        buf = BitAwareByteArray(bytearray((1, 2, 3)))
        buf.extend(bytearray((4, 5)))
        self.assertEqual([1, 2, 3, 4, 5], list(buf))

    def test_bitview_getitem__single_byte_bitslice(self):
        for i in range(0, 256):
            for j in range(0, 8):
                bv = BitView(bytearray([i]))
                self.assertEqual(list(bv[float(j) / 8:])[0], i >> j)

    def test_bitview_getitem__single_byte_bitslice_with_bits(self):
        for i in range(0, 256):
            for j in range(0, 8):
                bv = BitView(bytearray([i]))
                bv_slice = bv[float(j) / 8:]
                ba = bitarray(endian='little')
                ba.frombytes(chr(i) if PY2 else bytes([i]))
                ba_slice = ba[j:]
                self.assertEqualBitArrayBitView(ba_slice, bv_slice)

    def test_bitview__positive_slicing(self):
        for i in range(0, 100):
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

    def test_iadd_1(self):
        a = bytearray(b'\xd3\x94Q`\xb1\x93\x17\xed\xb2W\xa5\x00')
        b = bytearray(b'MK\xa3Li\xf9>\x039')
        bv1 = BitAwareByteArray(bytearray(a), start=0, stop=11.125)
        bv2 = BitView(bytearray(b), start=0, stop=8.75)
        bv1 += bv2

        a[-1] &= 0x01
        a[-1] |= (b[0] & 0x7F) << 1

        for i in range(len(b) - 1):
            a.append((b[i] >> 7) + ((b[i + 1] & 0x7F) << 1))

        self.assertEquals(list(bv1), list(a))

    def test_insert_zeros(self):
        bv = BitAwareByteArray(b"\x01", 0, 0.5)
        bv[0.5:1.5] = BitView(b"\x01")
        self.assertEqualBitArrayBitView(self._bitarray_from_bitstring('000000010001'), bv)

    def test_insert_zeros_1(self):
        bv = BitAwareByteArray(bytearray((0xFF, 0, 0, 0)))
        bv[0:0] = BitView(bytearray((0,)), 0, 0.5)
        self.assertEqualBitArrayBitView(self._bitarray_from_bitstring('000000000000000000000000111111110000'), bv)

    def test_insert_zeros_2(self):
        bv = BitAwareByteArray(bytearray())
        bv.zfill(0.5)
        bv[0.5:1.5] = BitView(b"\xff")
        bv.zfill(2.5)
        bv[2.5:3.5] = BitView(b"\x00")
        self.assertEqualBitArrayBitView(self._bitarray_from_bitstring('0000000000000000111111110000'), bv)

    def test_bitview_fetch_small(self):
        bv = BitView(b"\xFF\x00", 0, 6 * 0.125)
        self.assertEquals(bv[0], 63)

    def test_array_half_byte(self):
        a = BitAwareByteArray(bytearray(b'\x02'), start=0, stop=0.5)
        self.assertEquals(a[0], 2)
        self.assertEquals(list(a), [2])

    def assertEqualBitArrayBitView(self, ba, bv):
        self.assertEqual(ba.length(), 8 * bv.length())
        ba_bytes = self._bitarray_to_bytes(ba)
        if PY2:
            bv_bytes = str(bv)
        else:
            bv_bytes = bv.to_bytes()
        self.assertEqual(ba_bytes, bv_bytes)

    def _bitarray_from_bitstring(self, str):
        return bitarray("".join(reversed(str)), endian='little')

    def _create_random_bit_array(self):
        length_in_bits = random.randint(0, 8 * 16)
        return bitarray("".join(random.choice(('0', '1')) for i in range(length_in_bits)), endian='little')

    def _bitarray_to_bytes(self, b):
        copy = bitarray(b, endian='little')
        copy.fill()
        return bytearray(copy.tobytes())
