from infi.unittest import TestCase
from infi.instruct.buffer.reference import Reference, NumericReference, NumericBinaryExpression
from infi.instruct.buffer.reference import CyclicReferenceError

class NumberHolder:
    def __init__(self, n):
        self.n = n
        self.k = 10

class NumericAttrReference(Reference, NumericReference):
    def __init__(self, name):
        self.name = name

    def value(self, obj):
        return getattr(obj, self.name)

    def __repr__(self):
        return "num_ref({0})".format(self.name)

class ReferenceTestCase(TestCase):
    def test_numeric_reference(self):
        a = NumericAttrReference('n')
        self.assertEqual(42, a.value(NumberHolder(42)))

    def test_numeric_binary_expression_add__int(self):
        a = NumericAttrReference('n')
        self.assertEqual(42, (a + 5).value(NumberHolder(37)))

    def test_numeric_binary_expression_add__two_references(self):
        a = NumericAttrReference('n')
        b = NumericAttrReference('k')
        self.assertEqual(31, (a + b).value(NumberHolder(21)))

    def test_numeric_binary_expression_radd(self):
        a = NumericAttrReference('n')
        self.assertEqual(42, (5 + a).value(NumberHolder(37)))

    def test_numeric_binary_expression__type_error(self):
        a = NumericAttrReference('n')
        with self.assertRaises(TypeError):
            a + 'asdf'

    def test_numeric_binary_expression_add_repr(self):
        a = NumericAttrReference('n')
        self.assertEqual('(num_ref(n) + num_ref(n))', repr(a + a))
