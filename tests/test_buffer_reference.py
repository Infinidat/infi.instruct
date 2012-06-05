from infi.unittest import TestCase
from infi.instruct.buffer.reference import Reference, NumericReference, NumericGetAttrReference, Context
from infi.instruct.buffer.reference import NumericFuncReference, CyclicReferenceError

class NumberHolder:
    def __init__(self, n):
        self.n = n
        self.k = 10

class ReferenceTestCase(TestCase):
    def test_numeric_reference(self):
        obj = NumberHolder(42)
        a = NumericGetAttrReference(obj, 'n')
        self.assertEqual(42, a(Context()))

    def test_numeric_binary_expression_add__int(self):
        obj = NumberHolder(37)
        a = NumericGetAttrReference(obj, 'n')
        self.assertEqual(42, (a + 5)(Context()))

    def test_numeric_binary_expression_add__two_references(self):
        obj = NumberHolder(21)
        a = NumericGetAttrReference(obj, 'n')
        b = NumericGetAttrReference(obj, 'k')
        self.assertEqual(31, (a + b)(Context()))

    def test_numeric_binary_expression_radd(self):
        obj = NumberHolder(37)
        a = NumericGetAttrReference(obj, 'n')
        self.assertEqual(42, (5 + a)(Context()))

    def test_numeric_binary_expression__type_error(self):
        a = NumericGetAttrReference(None, 'n')
        with self.assertRaises(TypeError):
            a + 'asdf'

    def test_reference__cyclic_reference(self):
        a = NumericFuncReference(None)
        a.func_ref = a
        with self.assertRaises(CyclicReferenceError):
            a(Context())
