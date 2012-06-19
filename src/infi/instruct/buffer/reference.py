from contextlib import contextmanager
from numbers import Number
import threading
import operator

OPERATOR_TO_SYMBOL = {
    operator.add: "+",
    operator.sub: "-",
    operator.neg: "-"
}

class CyclicReferenceError(Exception):
    """Raised when discovering a cyclic reference."""

    MESSAGE = """Cyclic reference detected.
Reference cycle:
{cycle_str}
"""

    def __init__(self, ctx, last_ref):
        # Format the cycle as cycle_ref_1 -->\n cycle_ref_2 -->\n cycle_ref_3 -->\n...
        cycle = [ "  {0!r}".format(ref) for ref in ctx.call_stack + [ last_ref ] ]
        cycle_str = " -->\n".join(cycle)
        super(CyclicReferenceError, self).__init__(CyclicReferenceError.MESSAGE.format(cycle_str=cycle_str))

class Context(object):
    """Base class for working with references."""

    def __init__(self):
        self.cached_results = dict()
        self.call_nodes = set()
        self.call_stack = []
        self.exception_call_stack = None

    def format_exception_call_stack(self):
        return [ repr(line) for line in self.exception_call_stack ] if self.exception_call_stack is not None else []

class Reference(object):
    """
    An abstract reference. A reference is an object that will be resolved during packing or unpacking.
    This base class provides some convenience methods to handle references and expects subclasses to implement
    the value(obj) method.

    Be sure to override the following methods:
     * evaluate(self, ctx)
     * __safe_repr__(self)
    """

    def __call__(self, ctx):
        """
        Returns the value this reference is pointing to. This method uses 'obj' to resolve the reference and return
        the value this reference references.
        If the call was already made, it returns a cached result.
        It also makes sure there's no cyclic reference, and if so raises CyclicReferenceError.
        """
        if self in ctx.call_nodes:
            raise CyclicReferenceError(ctx, self)

        if self in ctx.cached_results:
            return ctx.cached_results[self]

        try:
            ctx.call_nodes.add(self)
            ctx.call_stack.append(self)

            result = self.evaluate(ctx)
            ctx.cached_results[self] = result
            return result
        except:
            if ctx.exception_call_stack is None:
                ctx.exception_call_stack = list(ctx.call_stack)
            raise
        finally:
            ctx.call_stack.pop()
            ctx.call_nodes.remove(self)

    def evaluate(self, ctx):
        raise NotImplementedError("Reference is an abstract class, you need to override evaluate(self, ctx) in {0}".
                                  format(type(self)))

    def __repr__(self):
        try:
            return self.__safe_repr__()
        except:
            return "({0}<{1}> repr error)".format(type(self), id(self))

    @classmethod
    def to_ref(self, ref):
        if isinstance(ref, Reference):
            return ref
        if isinstance(ref, Number):
            return NumberReference(ref)
        return ObjectReference(ref)

    def is_static(self):
        # We want to see if this reference can resolve w/o external dependencies, i.e. doesn't need anything from
        # the context. To do that, we have a "fake" context that raises an exception if someone tries to fetch
        # an attribute from it.
        class NotStaticObjectError(Exception):
            pass

        class StaticContext(Context):
            def __getattr__(self, name):
                raise NotStaticObjectError()

        ctx = StaticContext()
        try:
            self(ctx)
            return True
        except NotStaticObjectError:
            return False

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
    def __init__(self, ref, operator):
        self.ref = Reference.to_ref(ref)
        self.operator = operator

    def evaluate(self, ctx):
        return self.operator(self.ref(ctx))

    def __safe_repr__(self):
        op_sym = OPERATOR_TO_SYMBOL[self.operator] if self.operator in OPERATOR_TO_SYMBOL else repr(self.operator)
        return "{0}({1!r})".format(op_sym, self.ref)

class NumericBinaryExpression(Reference, NumericReference):
    """
    Binary expression support for references, e.g. ref('field') + 6.
    """
    def __init__(self, a, b, operator):
        self.a = Reference.to_ref(a)
        self.b = Reference.to_ref(b)
        self.operator = operator

    def evaluate(self, ctx):
        return self.operator(self.a(ctx), self.b(ctx))

    def __safe_repr__(self):
        op_sym = OPERATOR_TO_SYMBOL[self.operator] if self.operator in OPERATOR_TO_SYMBOL else repr(self.operator)
        return "({0!r} {1} {2!r})".format(self.a, op_sym, self.b)

class ObjectReference(Reference):
    """Holds a reference to an object."""

    def __init__(self, obj):
        self.obj = obj

    def evaluate(self, ctx):
        return self.obj

    def __safe_repr__(self):
        return "ref({0!r})".format(self.obj)

class NumberReference(ObjectReference, NumericReference):
    """Holds a reference to an object that we know is also a number."""

    def __safe_repr__(self):
        return "num_ref({0!r})".format(self.obj)

class FuncCallReference(Reference):
    """Holds a reference to a function call that will get executed when resolving."""

    def __init__(self, func, *args):
        self.func_ref = Reference.to_ref(func)
        self.arg_refs = [ Reference.to_ref(arg) for arg in args ]

    def evaluate(self, ctx):
        func = self.func_ref(ctx)
        args = [ arg_ref(ctx) for arg_ref in self.arg_refs ]
        return func(*args)

    def __safe_repr__(self):
        return "func_ref({0!r}({1}))".format(self.func_ref, ", ".join([ repr(arg) for arg in self.arg_refs ]))

class NumericFuncCallReference(FuncCallReference, NumericReference):
    """Holds a reference to a function call that returns a number."""

    def __safe_repr__(self):
        return "num_func_ref({0!r}({1}))".format(self.func_ref, ", ".join([ repr(arg) for arg in self.arg_refs ]))

class LengthFuncCallReference(NumericFuncCallReference):
    """Holds a reference to len(x) function call."""

    def __init__(self, arg):
        super(LengthFuncCallReference, self).__init__(len, arg)

    def __safe_repr__(self):
        return "len_ref({0!r})".format(self.arg_refs[0])

class GetAttrReference(FuncCallReference):
    """Holds a reference to getattr(object, attr_name) function call."""

    def __init__(self, object, attr_name):
        super(GetAttrReference, self).__init__(getattr, object, attr_name)

    def __safe_repr__(self):
        return "{0!r}.{1!r}".format(*self.arg_refs)

class NumericGetAttrReference(GetAttrReference, NumericReference):
    """Holds a reference to getattr(object, attr_name) function call where the attribute is a number."""
    pass

class SetAttrReference(FuncCallReference):
    """Holds a reference to setattr(object, attr_name, value) function call."""

    def __init__(self, object, attr_name, value):
        super(SetAttrReference, self).__init__(setattr, object, attr_name, value)

    def __safe_repr__(self):
        return "{0!r}.{1!r} = {2!r}".format(*self.arg_refs)

class SetAndGetAttrReference(FuncCallReference):
    """Holds a reference to setattr(object, attr_name, value) function call that returns value."""

    def __init__(self, object, attr_name, value):
        super(SetAndGetAttrReference, self).__init__(lambda obj, attr, val: setattr(obj, attr, val) or val,
                                                     object, attr_name, value)

    def __safe_repr__(self):
        return "set {0!r}.{1!r} = {2!r} then return {2!r}".format(*self.arg_refs)

class NumericSetAndGetAttrReference(SetAndGetAttrReference, NumericReference):
    """Holds a reference to setattr(object, attr_name, value) function call that returns a numeric value."""
    pass

class ReturnContextReference(Reference):
    """A reference that evaluates to the context itself (useful when using FuncCallReference)."""

    def evaluate(self, ctx):
        return ctx

    def __safe_repr__(self):
        return "ctx"

class ContextGetAttrReference(GetAttrReference):
    """A reference that returns an attribute from the context."""

    def __init__(self, attr_name):
        super(ContextGetAttrReference, self).__init__(ReturnContextReference(), attr_name)
