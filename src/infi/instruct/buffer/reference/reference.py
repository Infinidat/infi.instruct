import types
from numbers import Number
import operator

from infi.instruct.utils.safe_repr import safe_repr
from infi.instruct.errors import InstructError


OPERATOR_TO_SYMBOL = {
    operator.add: "+",
    operator.sub: "-",
    operator.neg: "-",
    operator.le: "<=",
    operator.lt: "<",
    operator.ge: ">=",
    operator.gt: ">",
    operator.eq: "==",
    operator.ne: "!="
}


def _repr_peel_obj_ref_for_str(ref):
    # Used to print attr names or other strings that shouldn't have the all ref('...') wrapping:
    if isinstance(ref, ObjectReference) and isinstance(ref.obj, str):
        return ref.obj
    else:
        return repr(ref)


class CyclicReferenceError(InstructError):
    """Raised when discovering a cyclic reference."""

    MESSAGE = """Cyclic reference detected.
Reference cycle:
{cycle_str}
"""

    def __init__(self, ctx, last_ref):
        # Format the cycle as cycle_ref_1 -->\n cycle_ref_2 -->\n cycle_ref_3 -->\n...
        cycle = ["  {0!r}".format(ref) for ref in ctx.call_stack + [last_ref]]
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
        return [repr(line) for line in self.exception_call_stack] if self.exception_call_stack is not None else []


class Reference(object):
    """
    An abstract reference. A reference is an object that will be resolved during packing or unpacking.
    This base class provides some convenience methods to handle references and expects subclasses to implement
    the evaluate(context) method.

    Be sure to override the following methods:
     * evaluate(self, ctx)
     * __safe_repr__(self)
    """
    def __init__(self, numeric):
        self.numeric = numeric

    def deref(self, ctx):
        """
        Returns the value this reference is pointing to. This method uses 'ctx' to resolve the reference and return
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

    def is_numeric(self):
        return self.numeric

    def __safe_repr__(self):
        raise NotImplementedError("Reference is an abstract class, you need to override __safe_repr__(self) in {0}".
                                  format(type(self)))

    def __repr__(self):
        try:
            return self.__safe_repr__()
        except:
            return "({0}<{1}> repr error)".format(type(self), id(self))

    @classmethod
    def to_ref(cls, ref):
        if isinstance(ref, Reference):
            return ref
        return ObjectReference(isinstance(ref, Number), ref)

    @classmethod
    def is_ref(cls, obj):
        return isinstance(obj, Reference)

    @classmethod
    def is_numeric_ref(cls, obj):
        return isinstance(obj, Reference) and obj.is_numeric()

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
            self.deref(ctx)
            return True
        except NotStaticObjectError:
            return False

    def __check_binary_expression_for_numeric(self, other):
        return self.is_numeric() and isinstance(other, Number)or (isinstance(other, Reference) and other.is_numeric())

    def __add__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.add)

    def __radd__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(other, self, operator.add)

    def __sub__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.sub)

    def __rsub__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(other, self, operator.sub)

    def __mul__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.mul)

    def __rmul__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(other, self, operator.mul)

    def __div__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.div)

    def __rdiv__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(other, self, operator.div)

    def __neg__(self):
        if not self.is_numeric(): return NotImplemented
        return NumericUnaryExpression(self, operator.neg)

    # FIXME: add rest of the operators, including unary ones
    def __le__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.le)

    def __lt__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.lt)

    def __ge__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.ge)

    def __gt__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.gt)

    def __eq__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.eq)

    def __ne__(self, other):
        if not self.__check_binary_expression_for_numeric(other): return NotImplemented
        return NumericBinaryExpression(self, other, operator.ne)


class NumericUnaryExpression(Reference):
    """
    Unary expression support for references, e.g. -ref('field').
    """
    def __init__(self, ref, operator):
        super(NumericUnaryExpression, self).__init__(numeric=True)
        self.ref = Reference.to_ref(ref)
        self.operator = operator

    def evaluate(self, ctx):
        return self.operator(self.ref.deref(ctx))

    def __safe_repr__(self):
        op_sym = OPERATOR_TO_SYMBOL[self.operator] if self.operator in OPERATOR_TO_SYMBOL else repr(self.operator)
        return "{0}({1!r})".format(op_sym, self.ref)

    def __nonzero__(self):
        raise NotImplementedError("not supported")


class NumericBinaryExpression(Reference):
    """
    Binary expression support for references, e.g. ref('field') + 6.
    """
    def __init__(self, a, b, operator):
        super(NumericBinaryExpression, self).__init__(numeric=True)
        self.a = Reference.to_ref(a)
        self.b = Reference.to_ref(b)
        self.operator = operator

    def evaluate(self, ctx):
        return self.operator(self.a.deref(ctx), self.b.deref(ctx))

    def __safe_repr__(self):
        op_sym = OPERATOR_TO_SYMBOL[self.operator] if self.operator in OPERATOR_TO_SYMBOL else repr(self.operator)
        return "({0!r} {1} {2!r})".format(self.a, op_sym, self.b)

    def __nonzero__(self):
        raise NotImplementedError("not supported")


class ObjectReference(Reference):
    """Holds a reference to an object."""

    def __init__(self, numeric, obj):
        super(ObjectReference, self).__init__(numeric)
        self.obj = obj

    def evaluate(self, ctx):
        return self.obj

    def __safe_repr__(self):
        if not isinstance(self.obj, Reference):
            return repr(self.obj)
        else:
            return "ref({0!r})".format(self.obj)


class NumericCastReference(Reference):
    def __init__(self, ref):
        super(NumericCastReference, self).__init__(True)
        self.ref = ref

    def evaluate(self, ctx):
        return self.ref.deref(ctx)

    def __safe_repr__(self):
        return "numeric({0!r})".format(self.ref)
