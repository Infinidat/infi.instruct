import types

from infi.instruct.utils.safe_repr import safe_repr

from .reference import Reference, ObjectReference


class FuncCallReference(Reference):
    """Holds a reference to a function call that will get executed when resolving."""

    def __init__(self, numeric, func, *args, **kwargs):
        super(FuncCallReference, self).__init__(numeric)
        self.func_ref = Reference.to_ref(func)
        self.arg_refs = [Reference.to_ref(arg) for arg in args]
        self.kwarg_refs = dict((k, Reference.to_ref(v)) for k, v in kwargs.items())

    def evaluate(self, ctx):
        func = self.func_ref.deref(ctx)
        assert callable(func), "func {0!r} from func_ref {1!r} is not callable".format(func, self.func_ref)
        args = [arg_ref.deref(ctx) for arg_ref in self.arg_refs]
        kwargs = dict((k, v_ref.deref(ctx)) for k, v_ref in self.kwarg_refs.items())
        return func(*args, **kwargs)

    def __safe_repr__(self):
        return "func_ref({0})".format(self._func_repr())

    def _func_repr(self):
        # Small hacks to make repr look better:
        if isinstance(self.func_ref, ObjectReference) \
                and isinstance(self.func_ref.obj, (types.FunctionType, types.MethodType)):
            func_ref_repr = self.func_ref.obj.func_name
        else:
            func_ref_repr = safe_repr(self.func_ref)
        return "{0}({1}))".format(func_ref_repr, self._args_and_kwargs_repr())

    def _args_and_kwargs_repr(self):
        return ", ".join((self._args_repr(), self._kwargs_repr()))

    def _args_repr(self):
        return ", ".join(safe_repr(arg) for arg in self.arg_refs)

    def _kwargs_repr(self):
        return ", ".join("{0}={1}".format(k, safe_repr(v_ref)) for k, v_ref in self.kwarg_refs.items())
