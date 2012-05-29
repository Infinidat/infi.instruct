from infi.unittest import TestCase
from infi.instruct.buffer.reference import Reference, NumericReference
from infi.instruct.buffer.range import ByteRangeFactory

class NumberHolder:
    def __init__(self, n):
        self.n = n
        self.k = 10

class NumericAttrReference(Reference, NumericReference):
    def __init__(self, name):
        self.name = name

    def value(self, obj):
        return getattr(obj, self.name)

    def needs_object_for_value(self):
        return True

bytes_ref = ByteRangeFactory()

class RangeTestCase(TestCase):
    def test_bytes_range__slice(self):
        range1 = bytes_ref[1:NumericAttrReference('n')]
        self.assertEqual([ slice(1, 10, 1) ], range1.value(NumberHolder(10)))

    def test_bytes_range__slice_binary_numeric_expression(self):
        range1 = bytes_ref[1:NumericAttrReference('n') + 5]
        self.assertEqual([ slice(1, 15, 1) ], range1.value(NumberHolder(10)))

    def test_bytes_range__binary_numeric_expression(self):
        range1 = bytes_ref[NumericAttrReference('n') + 5]
        self.assertEqual([ slice(15, 16, 1) ], range1.value(NumberHolder(10)))

    def test_bytes_range__list(self):
        range1 = bytes_ref[1, 5, 7]
        self.assertEqual([ slice(1, 2, 1), slice(5, 6, 1), slice(7, 8, 1) ], range1.value(None))

    def test_bytes_range__slice_in_list(self):
        range1 = bytes_ref[1:4, 5, 7]
        self.assertEqual([ slice(1, 4, 1), slice(5, 6, 1), slice(7, 8, 1) ], range1.value(None))

    def test_bytes_range__slice_needs_object_for_value(self):
        range1 = bytes_ref[1:4]
        self.assertFalse(range1.needs_object_for_value())

    def test_bytes_range__number_needs_object_for_value(self):
        range1 = bytes_ref[4]
        self.assertFalse(range1.needs_object_for_value())

    def test_bytes_range__list_needs_object_for_value(self):
        range1 = bytes_ref[1, 2, 3, 4]
        self.assertFalse(range1.needs_object_for_value())

    def test_bytes_range__slice_do_needs_object_for_value(self):
        range1 = bytes_ref[1:NumericAttrReference('n')]
        self.assertTrue(range1.needs_object_for_value())
