from .reference import Reference
from .builtins import GetAttrReference
from .func_call import FuncCallReference
from .contexts import ContextGetAttrReference


class FieldOrAttrReference(Reference):
    def __init__(self, numeric, name):
        super(FieldOrAttrReference, self).__init__(numeric)
        self.name = name

    def evaluate(self, ctx):
        return ctx.get_field(self.name).deref(ctx) if ctx.has_field(self.name) else getattr(ctx.obj, self.name)

    def __call__(self, *args, **kwargs):
        # this is a function call, so return a reference to a function call.
        return FuncCallReference(False, GetAttrReference(False, ContextGetAttrReference(False, 'obj'), self.name),
                                 *args, **kwargs)

    def __safe_repr__(self):
        return "field_or_attr_ref({!r})".format(self.name)


class SelfProxy(object):
    def __getattr__(self, name):
        # We choose by default that a forward reference is not numeric. If the user wants the reference to be numeric
        # he or she must explicitly say so by calling num_ref(...).
        return FieldOrAttrReference(False, name)
