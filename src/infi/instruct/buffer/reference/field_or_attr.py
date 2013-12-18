from .reference import Reference


class FieldOrAttrReference(Reference):
    def __init__(self, name):
        self.name = name

    def evaluate(self, ctx):
        return ctx.get_field(self.name)(ctx) if ctx.has_field(self.name) else getattr(ctx.obj, self.name)


class SelfProxy(object):
    def __getattr__(self, name):
        return FieldOrAttrReference(name)
