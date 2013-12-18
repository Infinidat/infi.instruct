import itertools

from infi.instruct.buffer.range import SequentialRangeList

from .reference import Reference, NumericReferenceMixin


class TotalSizeReference(Reference, NumericReferenceMixin):
    def evaluate(self, ctx):
        # First, we'll try a shortcut - if the size is static, we'll return that since we precalculated it.
        size = getattr(type(ctx.obj), 'byte_size', None)
        if size is not None:
            return size

        if ctx.is_pack():
            lists = [field.pack_absolute_position_ref(ctx) for field in ctx.fields]
            positions = SequentialRangeList(itertools.chain(*lists))
            result = positions.max_stop()  # total_size calculation
        else:
            result = max(self._unpack_position_list_for_field(ctx, field) for field in ctx.fields)

        assert result is not None
        return result

    def _unpack_position_list_for_field(self, ctx, field):
        result = field.unpack_absolute_position_ref.unpack_position_ref(ctx).byte_offset(field.unpack_ref(ctx)[1])
        return result

    def __safe_repr__(self):
        return "total_size"
