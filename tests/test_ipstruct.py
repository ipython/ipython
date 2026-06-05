"""Tests for IPython.utils.ipstruct.Struct"""
import pytest
from IPython.utils.ipstruct import Struct


def test_init_empty():
    s = Struct()
    assert s == {}


def test_init_kwargs():
    s = Struct(a=1, b=2)
    assert s["a"] == 1
    assert s.a == 1


def test_init_from_dict():
    s = Struct({"x": 10, "y": 20})
    assert s.x == 10


def test_init_from_struct():
    s1 = Struct(a=1)
    s2 = Struct(s1, b=2)
    assert s2.a == 1
    assert s2.b == 2


def test_setattr_getattr():
    s = Struct()
    s.foo = "bar"
    assert s.foo == "bar"
    assert s["foo"] == "bar"


def test_getattr_missing_raises():
    s = Struct(a=1)
    with pytest.raises(AttributeError):
        _ = s.missing_key


def test_setattr_protects_class_members():
    s = Struct()
    with pytest.raises(AttributeError):
        s.get = 10
    with pytest.raises(AttributeError):
        s.keys = []


def test_setitem_new_key():
    s = Struct()
    s["newkey"] = 42
    assert s["newkey"] == 42


def test_allow_new_attr_false_blocks_new_keys():
    s = Struct(a=1)
    s.allow_new_attr(False)
    s.a = 99  # existing key: ok
    assert s.a == 99
    with pytest.raises(AttributeError):
        s.new_key = 5
    with pytest.raises(KeyError):
        s["another"] = 5


def test_allow_new_attr_re_enable():
    s = Struct(a=1)
    s.allow_new_attr(False)
    s.allow_new_attr(True)
    s.b = 2  # should work now
    assert s.b == 2


def test_iadd_merge():
    s1 = Struct(a=1, b=2)
    s2 = Struct(a=99, c=3)
    s1 += s2
    assert set(s1.keys()) == {"a", "b", "c"}
    assert s1.a == 1  # merge preserves existing by default
    assert s1.c == 3


def test_add_returns_new_struct():
    s1 = Struct(a=1)
    s2 = Struct(b=2)
    s3 = s1 + s2
    assert isinstance(s3, Struct)
    assert s3.a == 1
    assert s3.b == 2
    assert "b" not in s1  # s1 unchanged


def test_sub_removes_keys():
    s1 = Struct(a=1, b=2, c=3)
    s2 = Struct(a=0, c=0)
    s3 = s1 - s2
    assert isinstance(s3, Struct)
    assert "a" not in s3
    assert "c" not in s3
    assert s3.b == 2


def test_isub():
    s1 = Struct(a=1, b=2)
    s2 = Struct(a=0)
    s1 -= s2
    assert "a" not in s1
    assert s1.b == 2


def test_copy():
    s = Struct(a=1, b=2)
    s2 = s.copy()
    assert isinstance(s2, Struct)
    assert s2 == s
    s2.a = 99
    assert s.a == 1  # original unchanged


def test_hasattr():
    s = Struct(a=1)
    assert s.hasattr("a")
    assert not s.hasattr("b")
    assert not s.hasattr("get")  # class member, not in data


def test_merge_default_preserves_existing():
    s = Struct(a=1, b=2)
    s.merge({"a": 99, "c": 3})
    assert s.a == 1  # preserved
    assert s.c == 3  # added


def test_merge_with_conflict_solver():
    s = Struct(a=1)
    s.merge({"a": 10}, {max: "a"})
    assert s.a == 10  # max(1, 10) = 10


def test_dict_method():
    s = Struct(a=1)
    assert s.dict() is s
