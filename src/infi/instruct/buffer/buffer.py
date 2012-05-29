from .field import Field, AttributeAccessorFactory
from .reference import Reference
from .io_buffer import InputBuffer, OutputBuffer

class BufferType(type):
    def __new__(cls, name, bases, attrs):
        # If we initialize our own class don't do any modifications.
        if name == "Buffer":
            return super(BufferType, cls).__new__(cls, name, bases, attrs)

        # We want to first put our own __init__ method that will initialize all the fields passed by kwargs and then
        # call the user's __init__ method (if exists) with args/kwargs left.
        # if "__init__" in attrs:
        #    user_init = attrs["__init__"]
        #    del attrs["__init__"]
        #else:
        #    user_init = None

        new_cls = super(BufferType, cls).__new__(cls, name, bases, attrs)

        visited_fields = set()
        serializable_fields = []
        def add_serializable_field(obj):
            if isinstance(obj, Field) and obj not in visited_fields:
                serializable_fields.append(obj)
                visited_fields.add(obj)

        for attr_name in dir(new_cls):
            attr = getattr(new_cls, attr_name)
            if isinstance(attr, Field):
                attr.name = attr_name # we may set the name here multiple times, but it's okay because it's the same
                if attr.value_getter is None:
                    attr.value_getter = AttributeAccessorFactory.create_getter(attr_name)
                if attr.value_setter is None:
                    attr.value_setter = AttributeAccessorFactory.create_setter(attr_name)
                Reference.dfs_traverse(attr, functor=add_serializable_field)

        setattr(new_cls, 'byte_size', cls.calc_byte_size(serializable_fields))
        setattr(new_cls, '__fields__', serializable_fields)
        return new_cls

    @classmethod
    def calc_byte_size(cls, fields):
        if any([ fld.position.needs_object_for_value() for fld in fields ]):
            return None

        max_len = 0
        for fld in fields:
            for slic in fld.position.value(None):
                if slic.start is None or slic.stop is None or slic.start < 0 or slic.stop < 0:
                    return None
            max_len = max(max_len, slic.stop, slic.start)
        return max_len

class Buffer(object):
    __metaclass__ = BufferType

    def __init__(self, *args, **kwargs):
        super(Buffer, self).__init__(*args, **kwargs)

    def pack(self):
        """Packs the object and returns a buffer representing the packed object."""
        output_buffer = OutputBuffer()
        for field in type(self).__fields__:
            field.pack(self, output_buffer)
        return output_buffer.get()

    def unpack(self, buffer):
        """Unpacks the object's fields from buffer."""
        input_buffer = InputBuffer(buffer)
        for field in type(self).__fields__:
            field.unpack(self, input_buffer)
        return self.calc_byte_size()

    def calc_byte_size(self):
        """Returns this instance's size. If the size has to be calculated it's equivalent to doing len(obj.pack())."""
        if type(self).byte_size is not None:
            return type(self).byte_size
        return len(self.pack())
