class StaticSerializer(object):
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
    def create_instance_from_stream(self, stream, *args, **kwargs):
        raise NotImplementedError()

    def write_instance_to_stream(self, instance, stream):
        raise NotImplementedError()

    def instance_repr(self, instance):
        return repr(instance)

    def sizeof(self):
        return None
