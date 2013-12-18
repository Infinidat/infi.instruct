def safe_repr(obj):
    """Returns a repr of an object and falls back to a minimal representation of type and ID if the call to repr raised
    an error.

    :param obj: object to safe repr
    :returns: repr string or '(type<id> repr error)' string
    :rtype: str
    """
    try:
        obj_repr = repr(obj)
    except:
        obj_repr = "({0}<{1}> repr error)".format(type(obj), id(obj))
    return obj_repr
