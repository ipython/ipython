"""Tests for IPython.utils.frame"""
import pytest
from IPython.utils.frame import extract_vars, extract_vars_above, extract_module_locals


def test_extract_vars_single():
    x = 42
    result = extract_vars("x")
    assert result == {"x": 42}


def test_extract_vars_multiple():
    a = 1
    b = "hello"
    result = extract_vars("a", "b")
    assert result == {"a": 1, "b": "hello"}


def test_extract_vars_missing_raises():
    with pytest.raises(KeyError):
        extract_vars("definitely_not_defined_xyz")


def test_extract_vars_above():
    def inner():
        return extract_vars_above("outer_var")

    outer_var = "found"
    result = inner()
    assert result == {"outer_var": "found"}


def test_extract_module_locals_returns_tuple():
    module, locals_ = extract_module_locals()
    assert hasattr(module, "__name__")
    assert isinstance(locals_, dict)


def test_extract_module_locals_module_name():
    module, _ = extract_module_locals()
    assert module.__name__ == __name__
