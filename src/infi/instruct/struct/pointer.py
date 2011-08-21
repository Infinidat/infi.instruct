from ..base import CallableReader

class ReadPointer(CallableReader):
    def __init__(self, name):
        super(ReadPointer, self).__init__(self._read_value)
        self.name = name

    def _read_value(self, stream, context):
        obj = context.get("struct", None)
        for field in obj._fields_:
            if getattr(field, "name", "") == self.name:
                self.size = field.marshal.size
        return getattr(obj, self.name)
