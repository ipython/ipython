"""Tests for IPython.core.display_trap."""

import sys

import pytest

from IPython.core.display_trap import DisplayTrap


def _custom_hook(value):
    pass


def test_display_trap_sets_displayhook():
    original_hook = sys.displayhook
    trap = DisplayTrap(hook=_custom_hook)
    with trap:
        assert sys.displayhook is _custom_hook
    assert sys.displayhook is original_hook


def test_display_trap_restores_displayhook_on_exit():
    original_hook = sys.displayhook
    with DisplayTrap(hook=_custom_hook):
        pass
    assert sys.displayhook is original_hook


def test_display_trap_returns_self_from_enter():
    trap = DisplayTrap(hook=_custom_hook)
    with trap as ctx:
        assert ctx is trap


def test_display_trap_is_active_inside_context():
    trap = DisplayTrap(hook=_custom_hook)
    assert trap.is_active is False
    with trap:
        assert trap.is_active is True
    assert trap.is_active is False


def test_display_trap_nested_only_sets_once():
    outer_hook = lambda v: None
    inner_hook = lambda v: None
    outer_trap = DisplayTrap(hook=outer_hook)
    inner_trap = DisplayTrap(hook=inner_hook)

    with outer_trap:
        assert sys.displayhook is outer_hook
        with inner_trap:
            assert sys.displayhook is inner_hook
        assert sys.displayhook is outer_hook


def test_display_trap_exception_propagates():
    original_hook = sys.displayhook
    with pytest.raises(RuntimeError):
        with DisplayTrap(hook=_custom_hook):
            raise RuntimeError("test")
    assert sys.displayhook is original_hook


def test_display_trap_nested_level_tracks_nesting():
    trap = DisplayTrap(hook=_custom_hook)
    assert trap._nested_level == 0
    with trap:
        assert trap._nested_level == 1
        with trap:
            assert trap._nested_level == 2
        assert trap._nested_level == 1
    assert trap._nested_level == 0
