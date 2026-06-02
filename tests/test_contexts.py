"""Tests for IPython.utils.contexts."""

import pytest

from IPython.utils.contexts import preserve_keys


def test_preserve_keys_restores_existing_key():
    d = {"a": 1, "b": 2}
    with preserve_keys(d, "a"):
        d["a"] = 99
    assert d["a"] == 1


def test_preserve_keys_deletes_new_key():
    d = {"a": 1}
    with preserve_keys(d, "new_key"):
        d["new_key"] = 42
    assert "new_key" not in d


def test_preserve_keys_preserves_unchanged_keys():
    d = {"a": 1, "b": 2, "c": 3}
    with preserve_keys(d, "a"):
        d["a"] = 99
    assert d["b"] == 2
    assert d["c"] == 3


def test_preserve_keys_missing_key_deleted_on_exit():
    d = {"a": 1}
    with preserve_keys(d, "missing"):
        assert "missing" not in d
        d["missing"] = "added"
    assert "missing" not in d


def test_preserve_keys_multiple_keys():
    d = {"x": 10, "y": 20}
    with preserve_keys(d, "x", "y", "z"):
        d["x"] = 100
        del d["y"]
        d["z"] = 30
    assert d["x"] == 10
    assert d["y"] == 20
    assert "z" not in d


def test_preserve_keys_restores_after_exception():
    d = {"a": 1}
    try:
        with preserve_keys(d, "a"):
            d["a"] = 99
            raise RuntimeError("test")
    except RuntimeError:
        pass
    assert d["a"] == 1


@pytest.mark.parametrize("original_value", [None, 0, False, "", [], {}])
def test_preserve_keys_restores_falsy_values(original_value):
    d = {"k": original_value}
    with preserve_keys(d, "k"):
        d["k"] = "replaced"
    assert d["k"] == original_value


def test_preserve_keys_no_keys_is_noop():
    d = {"a": 1}
    with preserve_keys(d):
        d["a"] = 99
    assert d["a"] == 99
