"""Tests for IPython.utils.frame"""
import collections.abc

from IPython.utils.frame import extract_module_locals


def test_extract_module_locals_returns_tuple():
    module, locals_ = extract_module_locals()
    assert hasattr(module, "__name__")
    # On Python 3.13+, f.f_locals returns FrameLocalsProxy, not dict
    assert isinstance(locals_, collections.abc.Mapping)


def test_extract_module_locals_module_name():
    module, _ = extract_module_locals()
    assert module.__name__ == __name__
