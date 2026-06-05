"""Tests for IPython.utils.terminal"""
import pytest
from unittest import mock

import IPython.utils.terminal as terminal_mod
from IPython.utils.terminal import (
    toggle_set_term_title,
    set_term_title,
    restore_term_title,
    get_terminal_size,
)


def test_get_terminal_size_returns_tuple():
    result = get_terminal_size()
    assert isinstance(result, tuple)
    assert len(result) == 2


@pytest.mark.parametrize("defaultx,defaulty", [
    (80, 25),
    (120, 40),
    (40, 10),
])
def test_get_terminal_size_defaults_used_when_no_tty(defaultx, defaulty):
    with mock.patch("IPython.utils.terminal._get_terminal_size") as m:
        m.return_value = (defaultx, defaulty)
        w, h = get_terminal_size(defaultx, defaulty)
    assert w == defaultx
    assert h == defaulty


def test_toggle_set_term_title_enables():
    original = terminal_mod.ignore_termtitle
    try:
        toggle_set_term_title(True)
        assert terminal_mod.ignore_termtitle is False
    finally:
        terminal_mod.ignore_termtitle = original


def test_toggle_set_term_title_disables():
    original = terminal_mod.ignore_termtitle
    try:
        toggle_set_term_title(False)
        assert terminal_mod.ignore_termtitle is True
    finally:
        terminal_mod.ignore_termtitle = original


def test_set_term_title_noop_when_ignored():
    original = terminal_mod.ignore_termtitle
    try:
        terminal_mod.ignore_termtitle = True
        with mock.patch("IPython.utils.terminal._set_term_title") as m:
            set_term_title("test title")
            m.assert_not_called()
    finally:
        terminal_mod.ignore_termtitle = original


def test_set_term_title_calls_impl_when_enabled():
    original = terminal_mod.ignore_termtitle
    try:
        terminal_mod.ignore_termtitle = False
        with mock.patch("IPython.utils.terminal._set_term_title") as m:
            set_term_title("test title")
            m.assert_called_once_with("test title")
    finally:
        terminal_mod.ignore_termtitle = original


def test_restore_term_title_noop_when_ignored():
    original = terminal_mod.ignore_termtitle
    try:
        terminal_mod.ignore_termtitle = True
        with mock.patch("IPython.utils.terminal._restore_term_title") as m:
            restore_term_title()
            m.assert_not_called()
    finally:
        terminal_mod.ignore_termtitle = original
