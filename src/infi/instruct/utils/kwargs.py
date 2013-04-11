def keep_kwargs_partial(func, *args, **keywords):
    """Like functools.partial but instead of using the new kwargs, keeps the old ones."""
    def newfunc(*fargs, **fkeywords):
        newkeywords = fkeywords.copy()
        newkeywords.update(keywords)
        return func(*(args + fargs), **newkeywords)
    newfunc.func = func
    newfunc.args = args
    newfunc.keywords = keywords
    return newfunc


def copy_and_remove_kwargs(kwargs, keys_to_remove):
    return dict((k, v) for k, v in kwargs.items() if k not in keys_to_remove)


def copy_defaults_and_override_with_kwargs(defaults, kwargs):
    d = defaults.copy()
    d.update(kwargs)
    return d


def copy_and_verify_fixed_kwargs(fixed_kwargs, kwargs):
    d = fixed_kwargs.copy()
    for k in fixed_kwargs.keys():
        assert k not in kwargs or kwargs[k] == d[k], "argument {0} must be {1} but instead is {2}".format(k, d[k], kwargs[k])
    d.update(kwargs)
    return d


def assert_kwarg_required(kwargs, key):
    assert key in kwargs, "{0} argument required but missing".format(key)


def assert_kwargs_not_conflicting(kwargs, key, conflicting_keys):
    if key in kwargs:
        assert not any(k in kwargs for k in conflicting_keys), \
            "{0} argument cannot be used with the following arguments: {1}".format(key, ", ".join(conflicting_keys))


def assert_kwarg_enum(kwargs, key, enum):
    if key in kwargs:
        assert kwargs[key] in enum, \
            "{0} argument must be one of: {1} but instead is {2}".format(key, ", ".join(enum), kwargs[key])


def assert_kwarg_exactly_single_out_of(kwargs, keys):
    keys_found = [k for k in keys if k in kwargs]
    if len(keys_found) == 0:
        assert False, "exactly one argument out of ({0}) is required but none were passed".format(", ".join(keys))
    else:
        assert len(keys_found) == 1, \
            "only one argument out of ({0}) is allowed but passed ({1})".format(", ".join(keys), ", ".join(keys_found))
