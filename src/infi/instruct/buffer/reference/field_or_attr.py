from .reference import Reference


class FieldOrAttrReference(Reference):
    def __init__(self, numeric, name):
        super(FieldOrAttrReference, self).__init__(numeric)
        self.name = name

    def evaluate(self, ctx):
        return ctx.get_field(self.name).deref(ctx) if ctx.has_field(self.name) else getattr(ctx.obj, self.name)


class SelfProxy(object):
    def __getattr__(self, name):
        # We choose by default that a forward reference is not numeric. If the user wants the reference to be numeric
        # he or she must explicitly say so by calling numeric_ref(...).
        return FieldOrAttrReference(False, name)
