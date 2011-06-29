from StringIO import StringIO

def obj_to_string(obj):
    stream = StringIO()
    type(obj).write_instance_to_stream(obj, stream)
    result = stream.getvalue()
    stream.close()
    return result

def string_to_obj(cls, string, *args, **kwargs):
    stream = StringIO(string)
    return cls.create_instance_from_stream(stream, *args, **kwargs)

    
