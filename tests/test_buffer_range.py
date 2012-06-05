from infi.unittest import TestCase
from infi.instruct.buffer.reference import Reference, NumericGetAttrReference, Context
from infi.instruct.buffer.range import RangeFactory, SequentialRange

class ObjectContext(Context):
    def __init__(self, obj):
        super(ObjectContext, self).__init__()
        self.obj = obj

class ObjectContextReference(Reference):
    def evaluate(self, ctx):
        return ctx.obj

    def __repr__(self):
        return "obj_ctx_ref"

class NumberHolder(object):
    def __init__(self, n):
        self.n = n
        self.k = 10

bytes_ref = RangeFactory()

class RangeTestCase(TestCase):
    def test_range_factory__slice_range_reference(self):
        range1 = bytes_ref[1:NumericGetAttrReference(ObjectContextReference(), 'n')]
        ctx = ObjectContext(NumberHolder(10))
        self.assertEqualRangeList([ slice(1, 10, 1) ], range1(ctx))

    def test_range_factory__slice_range_reference_binary_numeric_expression(self):
        range1 = bytes_ref[1:NumericGetAttrReference(ObjectContextReference(), 'n') + 5]
        ctx = ObjectContext(NumberHolder(10))
        self.assertEqualRangeList([ slice(1, 15, 1) ], range1(ctx))

    def test_range_factory__numeric_reference_binary_numeric_expression(self):
        range1 = bytes_ref[NumericGetAttrReference(ObjectContextReference(), 'n') + 5]
        ctx = ObjectContext(NumberHolder(10))
        self.assertEqualRangeList([ slice(15, 16, 1) ], range1(ctx))

    def test_range_factory__list_range_reference(self):
        range1 = bytes_ref[1, 5, 7]
        self.assertEqualRangeList([ slice(1, 2, 1), slice(5, 6, 1), slice(7, 8, 1) ], range1(Context()))

    def test_range_factory__slice_and_list(self):
        range1 = bytes_ref[1:4, 5, 7]
        self.assertEqualRangeList([ slice(1, 4, 1), slice(5, 6, 1), slice(7, 8, 1) ], range1(Context()))

    def test_sequential_range_list_length(self):
        self.assertEqual(6, SequentialRange.sum_length([ SequentialRange(0, 4), SequentialRange(-3, -1) ]))

    def test_sequential_range_list_length__relative(self):
        self.assertEqual(None, SequentialRange.sum_length([ SequentialRange(0, 4), SequentialRange(0, -1) ]))

    def assertEqualRangeList(self, a, b):
        self.assertEqual(a, [ r.to_slice() for r in b ])
