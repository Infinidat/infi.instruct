import struct
from infi.unittest import TestCase
from infi.instruct.buffer.reference import Reference, NumericReference, Context, LengthFuncReference
from infi.instruct.buffer.reference import NumericGetAttrReference, GetAttrReference
from infi.instruct.buffer.range import SequentialRange, ListRangeReference, SliceRangeReference
from infi.instruct.buffer.range import sequential_range_max_stop
from infi.instruct.buffer.field import OutputBufferSetReference
from infi.instruct.buffer.field import ContextGetAttrReference
from infi.instruct.buffer.serialize import UBInt32SerializeReference, StringSerializeReference
from infi.instruct.buffer.io_buffer import InputBuffer, OutputBuffer

class OutputContext(Context):
    def __init__(self, obj):
        super(OutputContext, self).__init__()
        self.obj = obj
        self.output_buffer = OutputBuffer()

class TotalSizeReference(Reference, NumericReference):
    def __init__(self, *refs):
        self.refs = refs

    def evaluate(self, ctx):
        m = 0
        for pos in [ pos_ref(ctx) for pos_ref in self.refs ]:
            print("TotalSizeReference.evaluate: pos={0}".format(repr(pos)))
            # FIXME: sequential_range_max_stop may return None - this is an error!
            m = max(m, sequential_range_max_stop(pos))
        print("TotalSizeReference.evaluate: result={0}".format(m))
        return m

    def get_children(self):
        return self.refs

class FieldTestCase(TestCase):
    class MyClass(object):
        def __init__(self, f_int, f_str):
            self.f_int = f_int
            self.f_str = f_str

    def test_field_building_blocks(self):
        # For unpack, it's:
        #   f_int = uint32(position=bytes[0:4], set_value=total_size - 4)
        #   f_str = str(position=[4:4 + f_int])
        # For pack, it's:
        #   f_int = uint32(position=bytes[0:4], set_value=total_size - 4)
        #   f_str = str(position=[4:4 + len(f_str field)])

        # Pack:
        f_str_get = GetAttrReference(ContextGetAttrReference('obj'), 'f_str')
        f_str_serialize = StringSerializeReference(f_str_get)
        f_str_position = \
          ListRangeReference([ SliceRangeReference(slice(4, 4 + LengthFuncReference(f_str_serialize))) ])
        f_str_buffer_set = OutputBufferSetReference(ContextGetAttrReference('output_buffer'),
                                                    f_str_serialize, f_str_position)

        f_int_position = ListRangeReference([ SliceRangeReference(slice(0, 4)) ])
        total_size = TotalSizeReference(f_int_position, f_str_position)
        f_int_get = total_size - 4
        f_int_serialize = UBInt32SerializeReference(f_int_get)
        f_int_buffer_set = OutputBufferSetReference(ContextGetAttrReference('output_buffer'),
                                                    f_int_serialize, f_int_position)

        obj = FieldTestCase.MyClass(0, 'hello world')
        ctx = OutputContext(obj)
        f_int_buffer_set(ctx)
        f_str_buffer_set(ctx)
        self.assertEqual(struct.pack(">L", len(obj.f_str)) + obj.f_str, ctx.output_buffer.get())

        # Unpack:


        # all_fields = WaitFor(f_int_buffer_set, f_str_buffer_set)

    # def test_field_pack(self):
    #     f_int = self._create_field('f_int', UBInt32Serialize, [ SequentialRange(0, 4) ])
    #     f_str = self._create_field('f_str', StringSerialize, [ SequentialRange(4, None) ])
    #     out = OutputBuffer()

    #     obj = FieldTestCase.MyClass(42, "kawabonga")
    #     f_int.pack(obj, out)
    #     f_str.pack(obj, out)
    #     self.assertEquals(struct.pack(">L", obj.f_int) +  obj.f_str, out.get())

    # def test_field_unpack(self):
    #     f_int = self._create_field('f_int', UBInt32Serialize, [ SequentialRange(0, 4) ])
    #     f_str = self._create_field('f_str', StringSerialize, [ SequentialRange(4, None) ])
    #     input = InputBuffer(struct.pack(">L", 42) + "kawabonga")

    #     obj = FieldTestCase.MyClass(0, "")
    #     f_int.unpack(obj, input)
    #     f_str.unpack(obj, input)
    #     self.assertEquals(42, obj.f_int)
    #     self.assertEquals("kawabonga", obj.f_str)

    # def test_numeric_field_reference(self):
    #     f_int = self._create_field_reference('f_int', UBInt32Serialize, [ SequentialRange(0, 4) ], cls=NumericFieldReference)
    #     self.assertEquals(10, f_int.value(FieldTestCase.MyClass(10, ''), Reference.OP_PACK))

    # def test_numeric_field_reference__add_expr(self):
    #     f_int = self._create_field_reference('f_int', UBInt32Serialize, [ SequentialRange(0, 4) ], cls=NumericFieldReference)
    #     self.assertEquals(14, (f_int + 4).value(FieldTestCase.MyClass(10, ''), Reference.OP_PACK))

    # def _create_field(self, name, serialize_class, position):
    #     return Field(AttributeAccessorFactory.create_getter(name), AttributeAccessorFactory.create_setter(name),
    #                  serialize_class.serialize, serialize_class.deserialize, position)

    # def _create_field_reference(self, name, serialize_class, position, cls=FieldReference):
    #     return cls(AttributeAccessorFactory.create_getter(name), AttributeAccessorFactory.create_setter(name),
    #                serialize_class.serialize, serialize_class.deserialize, position)
