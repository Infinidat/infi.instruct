from cStringIO import StringIO

class StaticSerializer(object):
    @classmethod
    def create_instance_from_string(cls, string, *args, **kwargs):
        io = StringIO(string)
        instance = cls.create_instance_from_stream(io, *args, **kwargs)
        io.close()
        return instance

    @classmethod
    def instance_to_string(cls, instance):
        io = StringIO()
        instance = cls.write_instance_to_stream(instance, io)
        result = io.getvalue()
        io.close()
        return result
        
    @classmethod
    def create_instance_from_stream(cls, stream, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def write_instance_to_stream(cls, instance, stream):
        raise NotImplementedError()

    @classmethod
    def instance_repr(cls, instance):
        return repr(instance)

    @classmethod
    def sizeof(cls):
        return None

class DynamicSerializer(object):
    def create_instance_from_string(self, string, *args, **kwargs):
        io = StringIO(string)
        instance = self.create_instance_from_stream(io, *args, **kwargs)
        io.close()
        return instance

    def instance_to_string(self, instance):
        io = StringIO()
        instance = self.write_instance_to_stream(instance, io)
        result = io.getvalue()
        io.close()
        return result

    def create_instance_from_stream(self, stream, *args, **kwargs):
        raise NotImplementedError()

    def write_instance_to_stream(self, instance, stream):
        raise NotImplementedError()

    def instance_repr(self, instance):
        return repr(instance)

    def sizeof(self):
        return None
