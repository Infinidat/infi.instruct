from infi.unittest import TestCase
from infi.instruct.buffer.reference import (Context, NumericGetAttrReference, NumericFuncCallReference,
                                            CyclicReferenceError, FuncCallReference, NumberReference)


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
        a = NumericFuncCallReference(None)
        a.func_ref = a
        with self.assertRaises(CyclicReferenceError):
            a(Context())

        repr(a)  # make sure it doesn't raise an exception

    def test_func_call_reference(self):
        def foo(value, add=0):
            return value + add

        foo_ref = FuncCallReference(foo, 5, add=7)
        self.assertEqual(12, foo_ref(Context()))

        foo_ref = FuncCallReference(foo, 5)
        self.assertEqual(5, foo_ref(Context()))

        foo_ref = FuncCallReference(foo, NumberReference(5), add=NumberReference(7))
        self.assertEqual(12, foo_ref(Context()))
