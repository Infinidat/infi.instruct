import itertools

from infi.instruct.buffer.range import SequentialRangeList

from .reference import Reference


class TotalSizeReference(Reference):
    def __init__(self):
        super(TotalSizeReference, self).__init__(True)

    def evaluate(self, ctx):
        # First, we'll try a shortcut - if the size is static, we'll return that since we precalculated it.
        size = getattr(type(ctx.obj), 'byte_size', None)
        if size is not None:
            return size

        if ctx.is_pack():
            lists = [field.pack_absolute_position_ref.deref(ctx) for field in ctx.fields]
            positions = SequentialRangeList(itertools.chain(*lists))
            result = positions.max_stop()  # total_size calculation
        else:
            # For each field we do the following and then take the maximum:
            #   We fetch the field's unpack size from unpack_ref (should already be cached).
            #   We then fetch the field's absolute position and calculate the byte offset from that.
            result = max(self._unpack_position_list_for_field(ctx, field) for field in ctx.fields)

        assert result is not None
        return result

    def _unpack_position_list_for_field(self, ctx, field):
        if field.unpack_if.deref(ctx):
            _, size = field.unpack_ref.deref(ctx)
            result = field.unpack_absolute_position_ref.deref(ctx).byte_offset(size)
            return result
        else:
            return 0

    def __safe_repr__(self):
        return "total_size"
