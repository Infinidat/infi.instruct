from infi.instruct.buffer.range import SequentialRangeList

from .reference import Reference


class AfterFieldReference(Reference):
    def __init__(self, field_ref):
        super(AfterFieldReference, self).__init__(True)
        self.field_ref = field_ref

    def evaluate(self, ctx):
        offset = None
        if ctx.is_pack():
            offset = SequentialRangeList(self.field_ref.pack_absolute_position_ref.deref(ctx)).max_stop()
        else:
            # This is a bit more tricky, since unpack_absolute_position_ref returns the length for the rest of the
            # buffer if it contains an open range.
            if self.field_ref.unpack_absolute_position_ref.is_open(ctx):
                # It's an open range, so we need to limit it by checking the _actual_ byte size the field used to unpack.
                # Since all reference results are cached, we can ask the unpack result again w/o performance problems.
                _, byte_size = self.field_ref.unpack_ref.deref(ctx)
                position_list = self.field_ref.unpack_absolute_position_ref.unpack_position_ref.deref(ctx)
                # Since we want the "highest" byte, we need to sort the ranges.
                offset = position_list.sorted().byte_offset(byte_size)
            else:
                offset = self.field_ref.unpack_absolute_position_ref.deref(ctx).max_stop()
        return offset

    def __safe_repr__(self):
        return "after({0})".format(self.field_ref.attr_name_ref.deref(Context()))
