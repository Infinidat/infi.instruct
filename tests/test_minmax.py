import sys
from infi.instruct.base import MinMax

def test_eq():
    assert MinMax(0, 10) == MinMax(0, 10)
    a = MinMax(0, 10)
    assert a == a

    assert MinMax(-1, 10) == MinMax(-5, 10)

    assert MinMax(0, sys.maxint + 10) == MinMax(-1, sys.maxint)

def test_add():
    assert (MinMax(0, 10) + MinMax(-5, 10)) == MinMax(0, 20)

def test_access():
    a = MinMax(-1, 1)
    assert a.min == 0
    assert a.max == 1
