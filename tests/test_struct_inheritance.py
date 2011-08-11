from infi.instruct import Struct, UBInt8

def test_struct_fields_inheritance():
    class Struct1(Struct):
        _fields_ = [ UBInt8("foo") ]

    class Struct2(Struct1):
        pass

    s = Struct1(foo=1)

def test_struct_init_inheritance_fails():
    class Struct1(Struct):
        _fields_ = [ UBInt8("foo"), UBInt8("bar") ]

        def __init__(self, foo):
            super(Struct1, self).__init__(foo=foo)

    class Struct2(Struct1):
        def __init__(self, bar):
            super(Struct2, self).__init__(1, bar=bar)

    try:
        s2 = Struct2(42)
        assert False
    except TypeError:
        pass

def test_struct_init_inheritance_ok_but_misleading():
    class Struct1(Struct):
        _fields_ = [ UBInt8("foo"), UBInt8("bar") ]

        def __init__(self, foo):
            super(Struct1, self).__init__()
            self.foo = foo

    class Struct2(Struct1):
        def __init__(self, bar):
            super(Struct2, self).__init__(1)
            self.bar = bar

    s2 = Struct2(42, foo=123)
    assert s2.foo == 1

def test_struct_init_inheritance_super():
    class Struct1(Struct):
        _fields_ = [ UBInt8("foo"), UBInt8("bar") ]

        def __init__(self, foo, bar):
            super(Struct1, self).__init__(foo=foo)
            self.bar = bar

    s1 = Struct1(1, 2)
    assert s1.foo == 1
    assert s1.bar == 2
