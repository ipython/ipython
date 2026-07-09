"""Tests for IPython.utils.syspathcontext."""

import sys

import pytest

from IPython.utils.syspathcontext import prepended_to_syspath

_FAKE_DIR = "/tmp/fake_test_dir_ipython_xyz_99999"


def test_prepended_adds_dir_to_sys_path():
    assert _FAKE_DIR not in sys.path
    with prepended_to_syspath(_FAKE_DIR):
        assert _FAKE_DIR in sys.path


def test_prepended_removes_dir_on_exit():
    with prepended_to_syspath(_FAKE_DIR):
        pass
    assert _FAKE_DIR not in sys.path


def test_prepended_dir_at_front_of_sys_path():
    with prepended_to_syspath(_FAKE_DIR):
        assert sys.path[0] == _FAKE_DIR


def test_prepended_returns_self():
    with prepended_to_syspath(_FAKE_DIR) as ctx:
        assert ctx is not None
        assert ctx.added is True


def test_prepended_already_in_path_not_duplicated():
    sys.path.insert(0, _FAKE_DIR)
    try:
        original_count = sys.path.count(_FAKE_DIR)
        with prepended_to_syspath(_FAKE_DIR):
            assert sys.path.count(_FAKE_DIR) == original_count
    finally:
        sys.path.remove(_FAKE_DIR)


def test_prepended_already_in_path_not_removed_on_exit():
    sys.path.insert(0, _FAKE_DIR)
    try:
        with prepended_to_syspath(_FAKE_DIR) as ctx:
            assert ctx.added is False
        assert _FAKE_DIR in sys.path
    finally:
        sys.path.remove(_FAKE_DIR)


def test_prepended_removes_after_exception():
    try:
        with prepended_to_syspath(_FAKE_DIR):
            raise RuntimeError("test exception")
    except RuntimeError:
        pass
    assert _FAKE_DIR not in sys.path


def test_prepended_exception_propagates():
    with pytest.raises(ValueError):
        with prepended_to_syspath(_FAKE_DIR):
            raise ValueError("should propagate")


def test_prepended_handles_concurrent_removal():
    with prepended_to_syspath(_FAKE_DIR) as ctx:
        sys.path.remove(_FAKE_DIR)
    # Should not raise ValueError even though dir was already removed
    assert _FAKE_DIR not in sys.path
