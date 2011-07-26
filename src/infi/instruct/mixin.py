import functools

mixin_cache = {}

def install_mixin_if(obj, mixin, condition):
    if not condition:
        return
    install_mixin(obj, mixin)

def install_mixin(obj, mixin):
    if isinstance(obj, mixin):
        return

    old_class = type(obj)
    if not (old_class, mixin) in mixin_cache:
        new_dict = {}
        for method in [ method for method in dir(mixin) if not method.startswith('__') ]:
            private_method = "_%s_%s" % (mixin.__name__, method)
            if hasattr(old_class, private_method):
                new_dict[method] = getattr(old_class, private_method)
        new_class = type('Mixin[%s, %s]' % (old_class.__name__, mixin.__name__), (old_class,  mixin), new_dict)
        mixin_cache[(old_class, mixin)] = new_class
    else:
        new_class = mixin_cache[(old_class, mixin)]

    obj.__class__ = new_class
