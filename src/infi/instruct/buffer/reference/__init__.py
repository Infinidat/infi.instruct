from .reference import (Reference, Context, CyclicReferenceError, NumericReferenceMixin,
                        ObjectReference, NumberReference)
from .func_call import FuncCallReference, NumericFuncCallReference
from .builtins import (LengthFuncCallReference, GetAttrReference, NumericGetAttrReference, SetAttrReference,
                       AssignAttrReference, NumericAssignAttrReference)
from .contexts import BufferContext, PackContext, UnpackContext, ReturnContextReference, ContextGetAttrReference
from .field import FieldReference, NumericFieldReference
from .field_or_attr import FieldOrAttrReference, SelfProxy
from .after_field import AfterFieldReference
from .total_size import TotalSizeReference
from .range import ByteRangeFactory

def func_call_ref_class(is_numeric):
    return NumericFuncCallReference if is_numeric else FuncCallReference


def assign_ref_class(is_numeric):
    return NumericAssignAttrReference if is_numeric else AssignAttrReference


def getattr_ref_class(is_numeric):
    return NumericGetAttrReference if is_numeric else GetAttrReference