from contextlib import contextmanager
from numbers import Number
import threading
import operator

OPERATOR_TO_SYMBOL = {
    operator.add: "+",
    operator.sub: "-"
}

class CyclicReferenceError(Exception):
    """Raised when discovering a cyclic reference."""

    def __init__(self):
        super(CyclicReferenceError, self).__init__("Cyclic reference detected")

class Reference(object):
    """
    An abstract reference. A reference is an object that will be resolved during serialization or deserialization.
    This base class provides some convenience methods to handle references and expects subclasses to implement
    the value(obj) method.
    """

    def value(self, obj):
        """
        Returns the value this reference is pointing to. Since the reference is "symobolic", this method receives
        the object to act upon.
        """
        raise NotImplementedError("Reference is an abstract class, you need to override value()")

    def needs_object_for_value(self):
        """
        Returns True if the reference can be computed with out the object, or False if it requires the object.
        If it doesn't require the object, you can call ref.value(None) and receive the computed value.
        """
        return any([ type(self).ref_needs_object_for_value(ref) for ref in self.get_children() ])

    def get_children(self):
        """
        Returns the list of children this references holds. The children may be references by themselves or
        other objects.
        """
        return []

    @classmethod
    def dereference(cls, ref, obj):
        """Returns the reference 'ref' resolved with object 'obj' or 'ref' itself if is not a reference."""
        return ref.value(obj) if isinstance(ref, Reference) else ref

    @classmethod
    def ref_needs_object_for_value(cls, ref):
        """Convenience method that returns True if 'ref' is a reference and needs the object to resolve."""
        return ref.needs_object_for_value() if isinstance(ref, Reference) else False

    @classmethod
    def references(cls, a, b):
        """Returns True if 'a' is a reference and it or one of its children references 'b'."""
        if not isinstance(a, Reference):
            return False

        result = False
        def predicate(obj):
            if obj == b:
                result = True

        cls.dfs_traverse(a, predicate)
        return result

    @classmethod
    def mutual_reference(cls, a, b):
        """Returns True if 'a' is a reference and references 'b', and 'b' is a reference and references 'a'."""
        return cls.references(a, b) and cls.references(b, a)

    @classmethod
    def dfs_traverse(cls, a, functor=lambda x: x):
        """Utility method that does DFS traversal on the reference tree and calls functor(ref) on each node."""
        if not isinstance(a, Reference):
            return
        for child in a.get_children():
            cls.dfs_traverse(child, functor)
        functor(a)

class NumericReference(object):
    """
    A numeric reference is a mixin that adds support for arithmetic operators, such as add/sub.
    It supports operations on itself (NumericReference) and operations involving numbers and numeric references.
    """

    def __add__(self, other):
        if not isinstance(other, (Number, NumericReference)):
            return NotImplemented
        return NumericBinaryExpression(self, other, operator.add)

    def __radd__(self, other):
        if not isinstance(other, (Number, NumericReference)):
            return NotImplemented
        return NumericBinaryExpression(other, self, operator.add)


    def __sub__(self, other):
        if not isinstance(other, (Number, NumericReference)):
            return NotImplemented
        return NumericBinaryExpression(self, other, operator.sub)

    def __rsub__(self, other):
        if not isinstance(other, (Number, NumericReference)):
            return NotImplemented
        return NumericBinaryExpression(other, self, operator.sub)

    def __neg__(self):
        return NumericUnaryExpression(self, operator.neg)

    # FIXME: add rest of the operators, including unary ones

class NumericUnaryExpression(Reference, NumericReference):
    """
    Unary expression support for references, e.g. -ref('field').
    """
    def __init__(self, a, op):
        self.a = a
        self.op = op

    def get_children(self):
        return [ self.a ]

    def value(self, obj):
        return self.op(Reference.dereference(self.a, obj))

    def __repr__(self):
        return "{0}({1})".format(repr(self.op), repr(self.a))

class NumericBinaryExpression(Reference, NumericReference):
    """
    Binary expression support for references, e.g. ref('field') + 6.
    """
    def __init__(self, a, b, op):
        if Reference.mutual_reference(a, b):
            raise CyclicReferenceError()

        self.a = a
        self.b = b
        self.op = op

    def value(self, obj):
        return self.op(Reference.dereference(self.a, obj), Reference.dereference(self.b, obj))

    def get_children(self):
        return [ self.a, self.b ]

    def __repr__(self):
        op_sym = OPERATOR_TO_SYMBOL[self.op] if self.op in OPERATOR_TO_SYMBOL else repr(self.op)
        return "({0} {1} {2})".format(repr(self.a), op_sym, repr(self.b))
