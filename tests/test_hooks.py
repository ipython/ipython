# -*- coding: utf-8 -*-
"""Tests for CommandChainDispatcher."""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from unittest import mock

import pytest

from IPython.core.error import TryNext
from IPython.core.hooks import CommandChainDispatcher
from IPython.core.hooks import editor as default_editor_hook

# -----------------------------------------------------------------------------
# Local utilities
# -----------------------------------------------------------------------------


# Define two classes, one which succeeds and one which raises TryNext. Each
# sets the attribute `called` to True when it is called.
class Okay(object):
    def __init__(self, message):
        self.message = message
        self.called = False

    def __call__(self):
        self.called = True
        return self.message


class Fail(object):
    def __init__(self, message):
        self.message = message
        self.called = False

    def __call__(self):
        self.called = True
        raise TryNext(self.message)


# -----------------------------------------------------------------------------
# Test functions
# -----------------------------------------------------------------------------


def test_command_chain_dispatcher_ff():
    """Test two failing hooks"""
    fail1 = Fail("fail1")
    fail2 = Fail("fail2")
    dp = CommandChainDispatcher([(0, fail1), (10, fail2)])

    with pytest.raises(TryNext) as e:
        dp()
    assert str(e.value) == "fail2"

    assert fail1.called is True
    assert fail2.called is True


def test_command_chain_dispatcher_fofo():
    """Test a mixture of failing and succeeding hooks."""
    fail1 = Fail("fail1")
    fail2 = Fail("fail2")
    okay1 = Okay("okay1")
    okay2 = Okay("okay2")

    dp = CommandChainDispatcher(
        [
            (0, fail1),
            # (5, okay1), # add this later
            (10, fail2),
            (15, okay2),
        ]
    )
    dp.add(okay1, 5)

    assert dp() == "okay1"

    assert fail1.called is True
    assert okay1.called is True
    assert fail2.called is False
    assert okay2.called is False


def test_command_chain_dispatcher_eq_priority():
    okay1 = Okay("okay1")
    okay2 = Okay("okay2")
    dp = CommandChainDispatcher([(1, okay1)])
    dp.add(okay2, 1)


def test_command_chain_dispatcher_empty_raises_trynext():
    dp = CommandChainDispatcher()
    with pytest.raises(TryNext):
        dp()


def test_command_chain_dispatcher_str():
    dp = CommandChainDispatcher()
    assert isinstance(str(dp), str)


def test_command_chain_dispatcher_iter():
    okay = Okay("ok")
    dp = CommandChainDispatcher([(0, okay)])
    items = list(dp)
    assert len(items) == 1
    assert items[0] == (0, okay)


@pytest.mark.parametrize("priorities,expected_order", [
    ([10, 5, 1], [1, 5, 10]),
    ([0, 0, 0], [0, 0, 0]),
    ([3, 1, 2], [1, 2, 3]),
])
def test_command_chain_dispatcher_sorted_by_priority(priorities, expected_order):
    funcs = [Okay(f"val{i}") for i in range(len(priorities))]
    dp = CommandChainDispatcher()
    for func, prio in zip(funcs, priorities):
        dp.add(func, prio)
    actual = [prio for prio, _ in dp]
    assert actual == expected_order


def test_command_chain_dispatcher_first_okay_stops_chain():
    """Once one func succeeds, later ones are NOT called."""
    fail = Fail("fail")
    okay = Okay("ok")
    late = Okay("late")
    dp = CommandChainDispatcher([(0, fail), (5, okay), (10, late)])
    result = dp()
    assert result == "ok"
    assert fail.called is True
    assert okay.called is True
    assert late.called is False


def test_command_chain_dispatcher_passes_args():
    results = []

    def capture(*args, **kwargs):
        results.append((args, kwargs))
        return "done"

    dp = CommandChainDispatcher()
    dp.add(capture)
    dp(1, 2, key="val")
    assert results == [((1, 2), {"key": "val"})]


# -----------------------------------------------------------------------------
# Tests for the default editor hook
# -----------------------------------------------------------------------------


class _FakeShell:
    """Minimal stand-in for the IPython shell, providing just `.editor`."""

    def __init__(self, editor):
        self.editor = editor


def test_default_editor_hook_quotes_filename_with_space():
    shell = _FakeShell(editor="vi")
    called = {}

    def fake_popen(cmd, **kwargs):
        called["cmd"] = cmd
        return mock.MagicMock(**{"wait.return_value": 0})

    with mock.patch("subprocess.Popen", fake_popen):
        default_editor_hook(shell, "the file", linenum=None)

    assert '"the file"' in called["cmd"]


def test_default_editor_hook_no_quotes_needed():
    shell = _FakeShell(editor="vi")
    called = {}

    def fake_popen(cmd, **kwargs):
        called["cmd"] = cmd
        return mock.MagicMock(**{"wait.return_value": 0})

    with mock.patch("subprocess.Popen", fake_popen):
        default_editor_hook(shell, "nofile.py", linenum=None)

    assert '"nofile.py"' not in called["cmd"]
    assert "nofile.py" in called["cmd"]


def test_default_editor_hook_quotes_editor_path_if_file(tmp_path):
    editor_path = tmp_path / "my editor.exe"
    editor_path.write_text("", encoding="utf-8")  # must exist for os.path.isfile
    shell = _FakeShell(editor=str(editor_path))
    called = {}

    def fake_popen(cmd, **kwargs):
        called["cmd"] = cmd
        return mock.MagicMock(**{"wait.return_value": 0})

    with mock.patch("subprocess.Popen", fake_popen):
        default_editor_hook(shell, "file.py", linenum=None)

    assert f'"{editor_path}"' in called["cmd"]


def test_default_editor_hook_quotes_filename_with_linenum():
    shell = _FakeShell(editor="vi")
    called = {}

    def fake_popen(cmd, **kwargs):
        called["cmd"] = cmd
        return mock.MagicMock(**{"wait.return_value": 0})

    with mock.patch("subprocess.Popen", fake_popen):
        default_editor_hook(shell, "the file", linenum=64)

    assert called["cmd"] == 'vi +64 "the file"'
