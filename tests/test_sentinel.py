"""Tests for IPython.utils.sentinel."""

from IPython.utils.sentinel import Sentinel


def test_sentinel_repr():
    s = Sentinel("MY_VALUE", "mymodule")
    assert repr(s) == "mymodule.MY_VALUE"


def test_sentinel_repr_with_dotted_module():
    s = Sentinel("MISSING", "IPython.utils")
    assert repr(s) == "IPython.utils.MISSING"


def test_sentinel_without_docstring():
    s = Sentinel("X", "mod")
    assert not hasattr(s, "__doc__") or s.__doc__ is None or "X" not in s.__doc__


def test_sentinel_with_docstring():
    s = Sentinel("X", "mod", docstring="This is X.")
    assert s.__doc__ == "This is X."


def test_sentinel_without_docstring_not_set():
    s = Sentinel("Y", "mod")
    assert not hasattr(s, "__doc__") or s.__doc__ is None


def test_sentinel_identity():
    s1 = Sentinel("X", "mod")
    s2 = Sentinel("X", "mod")
    # Two Sentinels with the same name are NOT the same object
    assert s1 is not s2


def test_sentinel_name_and_module_accessible():
    s = Sentinel("EMPTY", "IPython.utils.sentinel")
    assert s.name == "EMPTY"
    assert s.module == "IPython.utils.sentinel"
