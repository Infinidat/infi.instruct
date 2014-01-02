import itertools

from infi.instruct.utils.safe_repr import safe_repr

from .io_buffer import InputBuffer, OutputBuffer
from .reference import (Reference, Context, ContextGetAttrReference, ObjectReference,
                        FuncCallReference, FieldReference, GetAttrReference, AssignAttrReference)
from .range import SequentialRangeList


class PackAbsolutePositionReference(Reference):
    def __init__(self, field, pack_position_ref):
        super(PackAbsolutePositionReference, self).__init__(False)
        self.field = field
        self.pack_position_ref = pack_position_ref

    def is_open(self, ctx):
        return self.pack_position_ref.deref(ctx).is_open()

    def evaluate(self, ctx):
        position_list = self.pack_position_ref.deref(ctx)
        if position_list.has_overlaps():
            raise ValueError("field position list has overlapping ranges")

        if position_list.is_open():
            # We need the serialization result of this field to set the range. Note that we already checked if the
            # position has overlapping ranges, so there may be only a single open range.
            packed_field = self.field.pack_ref.deref(ctx)
            current_length = 0
            absolute_position_list = []
            for pos in position_list:
                abs_pos = pos.to_closed(pos.start + len(packed_field) - current_length)
                absolute_position_list.append(abs_pos)
                current_length += abs_pos.byte_length()
            return absolute_position_list
        else:
            return position_list

    def __safe_repr__(self):
        return "pack_abs_position({0!r}, {1!r})".format(self.field, self.position_list)


class UnpackAbsolutePositionReference(Reference):
    def __init__(self, field, unpack_position_ref):
        assert field is not None, "field is None"
        assert unpack_position_ref is not None, "unpack_position_ref is None"
        super(UnpackAbsolutePositionReference, self).__init__(False)
        self.field = field
        self.unpack_position_ref = unpack_position_ref

    def is_open(self, ctx):
        return self.unpack_position_ref.deref(ctx).is_open()

    def evaluate(self, ctx):
        position_list = self.unpack_position_ref.deref(ctx)
        if position_list.has_overlaps():
            raise ValueError("field position list has overlapping ranges")

        if position_list.is_open():
            buffer_len = ctx.input_buffer.length()
            return position_list.to_closed(buffer_len)

        return position_list

    def __safe_repr__(self):
        return "unpack_abs_position(field={0!r}, {1!r})".format(self.field, self.unpack_position_ref)


class InputBufferPartReference(Reference):
    def __init__(self, position_ref):
        super(InputBufferPartReference, self).__init__(False)
        self.position_ref = position_ref

    def evaluate(self, ctx):
        return ctx.input_buffer.get(self.position_ref.deref(ctx))

    def __safe_repr__(self):
        return "input_buffer[{0!r}]".format(self.position_ref)


class UnpackerReference(FuncCallReference):
    def __init__(self, numeric, unpacker, absolute_position_ref, *args, **kwargs):
        super(UnpackerReference, self).__init__(numeric, unpacker, InputBufferPartReference(absolute_position_ref),
                                                *args, **kwargs)

    def _args_repr(self):
        return ", ".join(["buffer", "position"] + [safe_repr(arg) for arg in self.arg_refs[2:]])


class FieldUnpackerReference(Reference):
    def __init__(self, unpacker_ref):
        super(FieldUnpackerReference, self).__init__(unpacker_ref.is_numeric())
        self.unpacker_ref = unpacker_ref

    def evaluate(self, ctx):
        return self.unpacker_ref.deref(ctx)[0]

    def __safe_repr__(self):
        return "field_unpack({0})".format(self.unpacker_ref._func_repr())


class SequentialRangeListByteLengthReference(FuncCallReference):
    def __init__(self, arg):
        super(SequentialRangeListByteLengthReference, self).__init__(True, SequentialRangeList.byte_length, arg)

    def __safe_repr__(self):
        return "byte_length_ref({0})".format(self._args_repr())


class PackSequentialRangeListByteLengthReference(SequentialRangeListByteLengthReference):
    """
    A short-circuit to make sure we don't end up in a cyclic reference if the packing position depends on the packing
    result.
    """
    def evaluate(self, ctx):
        if self.arg_refs[0].is_open(ctx):
            return None
        else:
            return super(PackSequentialRangeListByteLengthReference, self).evaluate(ctx)

    def __safe_repr__(self):
        return "pack_byte_length_ref({0})".format(self._args_repr())



class FieldReferenceBuilder(object):
    def __init__(self, numeric, set_before_pack, pack_if, set_after_unpack, unpack_if,
                 where, where_when_pack, where_when_unpack, unpack_after, default):
        if not (where or (where_when_pack and where_when_unpack)):
            raise ValueError("where or where_when_pack/unpack must be given")
        self.numeric = numeric
        self.set_before_pack = set_before_pack
        self.set_after_unpack = set_after_unpack
        self.pack_if = pack_if
        self.unpack_if = unpack_if
        self.where = where
        self.where_when_pack = where_when_pack
        self.where_when_unpack = where_when_unpack
        self.unpack_after = unpack_after
        self.default = default
        self.pack_size = None
        self.unpack_size = None

        self.get_obj_from_ctx_ref = ContextGetAttrReference(False, 'obj')

        self.resolve_static_where()
        self.create_field()
        self.set_field_position()
        self.set_field_pack_value_ref()

    def resolve_static_where(self):
        def resolve_static_ref(ref):
            range_list = None
            if ref.is_static():
                range_list = ref.deref(Context())
            return range_list.byte_length() if range_list is not None else None

        if self.where is not None:
            assert self.where_when_pack is None and self.where_when_unpack is None
            self.pack_size = self.unpack_size = resolve_static_ref(self.where)

        if self.where_when_pack is not None:
            assert self.where is None and self.where_when_unpack is not None
            self.pack_size = resolve_static_ref(self.where_when_unpack)

        if self.where_when_unpack is not None:
            assert self.where is None and self.where_when_pack is not None
            self.unpack_size = resolve_static_ref(self.where_when_unpack)

        if self.pack_size is not None and self.unpack_size is not None:
            assert self.pack_size == self.unpack_size

    def create_field(self):
        # When we first create a field reference we don't know the field name yet. When __new__ will get called
        # on Buffer, it will fill it in for us.
        self.field = FieldReference(self.numeric, None)
        self.field.default = self.default
        self.field.pack_if = Reference.to_ref(self.pack_if) if self.pack_if is not None else Reference.to_ref(True)
        self.field.unpack_if = Reference.to_ref(self.unpack_if) if self.unpack_if is not None else Reference.to_ref(True)

    def set_field_position(self):
        if self.where is not None:
            pack_position_ref = unpack_position_ref = self.where
        else:
            pack_position_ref = self.where_when_pack
            unpack_position_ref = self.where_when_unpack

        self.field.pack_absolute_position_ref = PackAbsolutePositionReference(self.field, pack_position_ref)
        self.field.unpack_absolute_position_ref = UnpackAbsolutePositionReference(self.field, unpack_position_ref)

    def set_packer(self, packer, **kwargs):
        pack_kwargs = dict(byte_size=PackSequentialRangeListByteLengthReference(self.field.pack_absolute_position_ref),
                           pack_size=self.pack_size)
        pack_kwargs.update(kwargs)
        self.field.pack_ref = FuncCallReference(self.numeric, packer, self.field.pack_value_ref, **pack_kwargs)

    def set_unpacker(self, unpacker, **kwargs):
        unpack_kwargs = dict(byte_size=SequentialRangeListByteLengthReference(self.field.unpack_absolute_position_ref),
                             unpack_size=self.unpack_size)
        unpack_kwargs.update(kwargs)

        self.field.unpack_ref = UnpackerReference(self.numeric, unpacker, self.field.unpack_absolute_position_ref,
                                                  **unpack_kwargs)

    def create(self):
        self.set_field_unpack_value_ref()
        self.set_field_unpack_after()
        return self.field

    def set_field_pack_value_ref(self):
        if self.set_before_pack is not None:
            if not isinstance(self.set_before_pack, Reference):
                if callable(self.set_before_pack):
                    pack_value_ref = FuncCallReference(self.numeric, self.set_before_pack, self.get_obj_from_ctx_ref)
                else:
                    pack_value_ref = ObjectReference(self.numeric, self.set_before_pack)
            else:
                pack_value_ref = self.set_before_pack
            self.field.pack_value_ref = AssignAttrReference(self.numeric, self.get_obj_from_ctx_ref,
                                                            self.field.attr_name_ref, pack_value_ref)
        else:
            self.field.pack_value_ref = GetAttrReference(self.numeric, self.get_obj_from_ctx_ref,
                                                         self.field.attr_name_ref)

    def set_field_unpack_value_ref(self):
        field_unpack_ref = FieldUnpackerReference(self.field.unpack_ref)
        if self.set_after_unpack is not None:
            if not isinstance(self.set_after_unpack, Reference):
                unpack_value_ref = FuncCallReference(self.numeric, self.set_after_unpack, field_unpack_ref)
        else:
            unpack_value_ref = AssignAttrReference(self.numeric, self.get_obj_from_ctx_ref, self.field.attr_name_ref,
                                                   field_unpack_ref)

        self.field.unpack_value_ref = unpack_value_ref

    def set_field_unpack_after(self):
        if self.unpack_after is None:
            self.unpack_after = []
        elif not isinstance(self.unpack_after, (list, tuple)):
            self.unpack_after = [self.unpack_after]

        for unpack_after_field in self.unpack_after:
            assert isinstance(unpack_after_field, FieldReference)

        self.field.unpack_after = self.unpack_after
