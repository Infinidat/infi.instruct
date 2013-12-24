from infi.unittest import TestCase
from infi.instruct.buffer.reference import Reference, GetAttrReference, Context
from infi.instruct.buffer.range import SequentialRange, SequentialRangeList
from infi.instruct.buffer.reference.range import ByteRangeFactory

class ObjectContext(Context):
    def __init__(self, obj):
        super(ObjectContext, self).__init__()
        self.obj = obj

class ObjectContextReference(Reference):
    def __init__(self):
        super(ObjectContextReference, self).__init__(False)

    def evaluate(self, ctx):
        return ctx.obj

    def __repr__(self):
        return "obj_ctx_ref"

class NumberHolder(object):
    def __init__(self, n):
        self.n = n
        self.k = 10

bytes_ref = ByteRangeFactory()

class RangeTestCase(TestCase):
    def test_range_factory__slice_range_reference(self):
        range1 = bytes_ref[1:GetAttrReference(True, ObjectContextReference(), 'n')]
        ctx = ObjectContext(NumberHolder(10))
        self.assertEqualRangeList([ (1, 10) ], range1.deref(ctx))

    def test_range_factory__slice_range_reference_binary_numeric_expression(self):
        range1 = bytes_ref[1:GetAttrReference(True, ObjectContextReference(), 'n') + 5]
        ctx = ObjectContext(NumberHolder(10))
        self.assertEqualRangeList([ (1, 15) ], range1.deref(ctx))

    def test_range_factory__numeric_reference_binary_numeric_expression(self):
        range1 = bytes_ref[GetAttrReference(True, ObjectContextReference(), 'n') + 5]
        ctx = ObjectContext(NumberHolder(10))
        self.assertEqualRangeList([ (15, 16) ], range1.deref(ctx))

    def test_range_factory__list_range_reference(self):
        range1 = bytes_ref[1, 5, 7]
        self.assertEqualRangeList([ (1, 2), (5, 6), (7, 8) ], range1.deref(Context()))

    def test_range_factory__slice_and_list(self):
        range1 = bytes_ref[1:4, 5, 7]
        self.assertEqualRangeList([ (1, 4), (5, 6), (7, 8) ], range1.deref(Context()))

    def test_bit__numeric(self):
        range1 = bytes_ref[3:4].bits[5]
        self.assertEqualRangeList([ (3 + 5.0 / 8, 3 + 6.0 / 8) ], range1.deref(Context()))

    def test_bit__numeric_out_of_range(self):
        range1 = bytes_ref[3:4].bits[5:9]
        with self.assertRaises(ValueError):
            range1.deref(Context())

    def test_sequential_range_list_length(self):
        self.assertEqual(6, SequentialRangeList([ SequentialRange(0, 4), SequentialRange(1, 3) ]).byte_length())

    def test_sequential_range_list_overlaps(self):
        self.assertTrue(SequentialRangeList([ SequentialRange(0, 4), SequentialRange(1, 3) ]).has_overlaps())
        self.assertTrue(SequentialRangeList([ SequentialRange(1, 4), SequentialRange(0, 2) ]).has_overlaps())
        self.assertTrue(SequentialRangeList([ SequentialRange(1, 4), SequentialRange(0, 5) ]).has_overlaps())
        self.assertFalse(SequentialRangeList([ SequentialRange(0, 4), SequentialRange(4, 5) ]).has_overlaps())
        self.assertFalse(SequentialRangeList([ SequentialRange(3, 4), SequentialRange(1, 3) ]).has_overlaps())

    def assertEqualRangeList(self, a, b):
        self.assertEqual([ slice(s[0], s[1], 1) for s in a ], [ r.to_slice() for r in b ])
