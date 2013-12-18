from .reference import Reference, NumericReferenceMixin


class FieldReference(Reference):
    # Although not strictly a ref, we use attr_name as a ref because of how we pack - we create a reference to the
    # packed representation.
    attr_name_ref = None
    pack_value_ref = None
    unpack_value_ref = None
    pack_ref = None
    unpack_ref = None
    pack_absolute_position_ref = None
    unpack_absolute_position_ref = None
    unpack_after = None
    default = None

    def init(self, name):
        self.attr_name_ref.obj = name

    def is_initialized(self):
        return self.attr_name_ref.obj is not None

    def attr_name(self):
        return self.attr_name_ref.obj

    def evaluate(self, ctx):
        if ctx.is_pack():
            return self.pack_value_ref(ctx)
        else:
            return self.unpack_value_ref(ctx)

    def __safe_repr__(self):
        return "field_ref({0!r})".format(self.attr_name_ref.obj)


class NumericFieldReference(FieldReference, NumericReferenceMixin):
    def __safe_repr__(self):
        return "num_field_ref({0!r})".format(self.attr_name_ref.obj)
