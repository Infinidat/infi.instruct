from .func_call import FuncCallReference, FuncCallReference
from .reference import _repr_peel_obj_ref_for_str


class LengthFuncCallReference(FuncCallReference):
    """Holds a reference to len(x) function call."""

    def __init__(self, arg):
        super(LengthFuncCallReference, self).__init__(True, len, arg)

    def __safe_repr__(self):
        return "len_ref({0!r})".format(self.arg_refs[0])


class GetAttrReference(FuncCallReference):
    """Holds a reference to getattr(object, attr_name) function call."""

    def __init__(self, numeric, object, attr_name):
        super(GetAttrReference, self).__init__(numeric, getattr, object, attr_name)

    def __safe_repr__(self):
        # small hacks to make repr look better:
        arg_ref_repr = _repr_peel_obj_ref_for_str(self.arg_refs[1])
        return "{0!r}.{1}".format(self.arg_refs[0], arg_ref_repr)


class SetAttrReference(FuncCallReference):
    """Holds a reference to varient setattr(object, attr_name, value) function call."""

    def __init__(self, object, attr_name, value):
        super(SetAttrReference, self).__init__(False, setattr, object, attr_name, value)

    def __safe_repr__(self):
        # small hacks to make repr look better:
        arg_ref_repr = _repr_peel_obj_ref_for_str(self.arg_refs[1])
        return "(void) {0!r}.{1} = {2!r}".format(self.arg_refs[0], arg_ref_repr, self.arg_refs[2])


class AssignAttrReference(FuncCallReference):
    """Mimicks rvalue assignment (x = y) so you can chain this to other calls/references."""

    def __init__(self, numeric, object, attr_name, value):
        super(AssignAttrReference, self).__init__(numeric, lambda obj, attr, val: setattr(obj, attr, val) or val,
                                                  object, attr_name, value)

    def __safe_repr__(self):
        arg_ref_repr = _repr_peel_obj_ref_for_str(self.arg_refs[1])
        return "{0!r}.{1} = {2!r}".format(self.arg_refs[0], arg_ref_repr, self.arg_refs[2])


class MinFuncCallReference(FuncCallReference):
    """Holds a reference to min(*args) function call."""
    def __init__(self, *args):
        super(MinFuncCallReference, self).__init__(True, min, *args)

    def __safe_repr__(self):
        return "min_ref({0})".format(self._args_repr())


class MaxFuncCallReference(FuncCallReference):
    """Holds a reference to max(*args) function call."""
    def __init__(self, *args):
        super(MaxFuncCallReference, self).__init__(True, max, *args)

    def __safe_repr__(self):
        return "max_ref({0})".format(self._args_repr())