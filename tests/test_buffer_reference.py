from infi.unittest import TestCase
from infi.instruct.buffer.reference import (Context, GetAttrReference, FuncCallReference, ObjectReference,
                                            CyclicReferenceError)


class NumberHolder:
    def __init__(self, n):
        self.n = n
        self.k = 10


class ReferenceTestCase(TestCase):
    def test_numeric_reference(self):
        obj = NumberHolder(42)
        a = GetAttrReference(True, obj, 'n')
        self.assertEqual(42, a.deref(Context()))

    def test_numeric_binary_expression_add__int(self):
        obj = NumberHolder(37)
        a = GetAttrReference(True, obj, 'n')
        self.assertEqual(42, (a + 5).deref(Context()))

    def test_numeric_binary_expression_add__two_references(self):
        obj = NumberHolder(21)
        a = GetAttrReference(True, obj, 'n')
        b = GetAttrReference(True, obj, 'k')
        self.assertEqual(31, (a + b).deref(Context()))

    def test_numeric_binary_expression_radd(self):
        obj = NumberHolder(37)
        a = GetAttrReference(True, obj, 'n')
        self.assertEqual(42, (5 + a).deref(Context()))

    def test_numeric_binary_expression__type_error(self):
        a = GetAttrReference(True, None, 'n')
        with self.assertRaises(TypeError):
            a + 'asdf'

    def test_reference__cyclic_reference(self):
        a = FuncCallReference(True, None)
        a.func_ref = a
        with self.assertRaises(CyclicReferenceError):
            a.deref(Context())

        repr(a)  # make sure it doesn't raise an exception

    def test_func_call_reference(self):
        def foo(value, add=0):
            return value + add

        foo_ref = FuncCallReference(True, foo, 5, add=7)
        self.assertEqual(12, foo_ref.deref(Context()))

        foo_ref = FuncCallReference(True, foo, 5)
        self.assertEqual(5, foo_ref.deref(Context()))

        foo_ref = FuncCallReference(True, foo, ObjectReference(True, 5), add=ObjectReference(True, 7))
        self.assertEqual(12, foo_ref.deref(Context()))

    def test_numeric_operators(self):
        a = ObjectReference(True, 5)
        b = ObjectReference(True, 4)
        with self.assertRaises(NotImplementedError):
            self.assertTrue(a==a)

