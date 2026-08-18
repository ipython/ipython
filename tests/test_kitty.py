import os
import subprocess
import sys

import pytest
from pathlib import Path


class DummyStdout:
    def write(self, *args, **kwargs):
        pass

    def flush(self):
        pass


class StdoutWithNonCallableIsatty(DummyStdout):
    isatty = False


class StdoutTTY(DummyStdout):
    def isatty(self):
        return True


def test_supports_kitty_graphics_handles_stdout_without_callable_isatty(monkeypatch):
    from IPython.core import kitty

    monkeypatch.setattr(sys, "platform", "linux")
    for stdout in (DummyStdout(), StdoutWithNonCallableIsatty()):
        monkeypatch.setattr(sys, "stdout", stdout)
        assert kitty._supports_kitty_graphics() is False


def test_import_ipython_handles_stdout_without_isatty():
    code = """
import sys

class DummyFile:
    def write(self, *args, **kwargs):
        pass

    def flush(self):
        pass

sys.stdout = DummyFile()
import IPython
"""
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_supports_kitty_graphics_handles_psutil_access_denied(monkeypatch):
    """Detection must not crash when the process tree is inaccessible.

    On shared multi-user systems /proc is often mounted with ``hidepid``
    (common on HPC clusters), so walking up to an ancestor process owned by
    another user makes psutil raise AccessDenied. This must be treated as
    "unsupported" rather than aborting the import of IPython.
    """
    import psutil

    from IPython.core import kitty

    # "darwin" so that detection takes the psutil branch rather than /proc.
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(sys, "stdout", StdoutTTY())

    class DeniedProcess:
        def parent(self):
            raise psutil.AccessDenied(pid=1)

        def name(self):
            raise psutil.AccessDenied(pid=1)

    monkeypatch.setattr(psutil, "Process", lambda *args, **kwargs: DeniedProcess())

    assert kitty._supports_kitty_graphics() is False


def test_kitty_graphics_forced_on(monkeypatch):
    """IPYTHON_KITTY_GRAPHICS=1 states support without probing anything."""
    import psutil

    from IPython.core import kitty

    monkeypatch.setenv("IPYTHON_KITTY_GRAPHICS", "1")

    def fail(*args, **kwargs):
        raise AssertionError("detection must be skipped when forced")

    monkeypatch.setattr(psutil, "Process", fail)
    monkeypatch.setattr(sys, "stdout", DummyStdout())  # not even a tty

    assert kitty._supports_kitty_graphics() is True


def test_kitty_graphics_forced_off(monkeypatch):
    """IPYTHON_KITTY_GRAPHICS=0 wins over a terminal that does support it."""
    import psutil

    from IPython.core import kitty

    monkeypatch.setenv("IPYTHON_KITTY_GRAPHICS", "0")

    def fail(*args, **kwargs):
        raise AssertionError("detection must be skipped when forced")

    monkeypatch.setattr(psutil, "Process", fail)
    monkeypatch.setattr(sys, "stdout", StdoutTTY())

    assert kitty._supports_kitty_graphics() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE"])
def test_kitty_graphics_force_true_spellings(monkeypatch, value):
    from IPython.core import kitty

    monkeypatch.setenv("IPYTHON_KITTY_GRAPHICS", value)
    assert kitty._forced_kitty_graphics() is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE"])
def test_kitty_graphics_force_false_spellings(monkeypatch, value):
    from IPython.core import kitty

    monkeypatch.setenv("IPYTHON_KITTY_GRAPHICS", value)
    assert kitty._forced_kitty_graphics() is False


@pytest.mark.parametrize("value", ["", None])
def test_kitty_graphics_unset_autodetects(monkeypatch, value):
    from IPython.core import kitty

    if value is None:
        monkeypatch.delenv("IPYTHON_KITTY_GRAPHICS", raising=False)
    else:
        monkeypatch.setenv("IPYTHON_KITTY_GRAPHICS", value)
    assert kitty._forced_kitty_graphics() is None


def test_kitty_graphics_bad_value_warns_and_autodetects(monkeypatch):
    """A typo must not silently disable (or enable) graphics."""
    from IPython.core import kitty

    monkeypatch.setenv("IPYTHON_KITTY_GRAPHICS", "yes-please")
    with pytest.warns(UserWarning, match="IPYTHON_KITTY_GRAPHICS"):
        assert kitty._forced_kitty_graphics() is None


def _fake_proc(tree):
    """Build a `_read_proc_stat` replacement from a ``{pid: (name, ppid)}`` map.

    A pid missing from the map raises `PermissionError`, which is what
    ``hidepid`` gives for an ancestor owned by another user.
    """

    def read(pid):
        try:
            name, ppid = tree[pid]
        except KeyError:
            raise PermissionError(13, "Permission denied") from None
        return f"{pid} ({name}) S {ppid} 0 0 0 -1 0".encode()

    return read


def test_proc_ancestor_names_walks_up_to_pid_1(monkeypatch):
    from IPython.core import kitty

    monkeypatch.setattr(os, "getppid", lambda: 42)
    monkeypatch.setattr(
        kitty,
        "_read_proc_stat",
        _fake_proc({42: ("kitty", 7), 7: ("login", 1), 1: ("systemd", 0)}),
    )
    assert list(kitty._proc_ancestor_names()) == ["kitty", "login", "systemd"]


def test_proc_ancestor_names_handles_names_with_spaces_and_parens(monkeypatch):
    """`comm` is not escaped in /proc/<pid>/stat, so parse from the last ')'."""
    from IPython.core import kitty

    monkeypatch.setattr(os, "getppid", lambda: 5)
    monkeypatch.setattr(
        kitty,
        "_read_proc_stat",
        _fake_proc({5: ("we (ird) name", 1), 1: ("init", 0)}),
    )
    assert list(kitty._proc_ancestor_names()) == ["we (ird) name", "init"]


def test_proc_ancestor_names_stops_when_an_ancestor_is_unreadable(monkeypatch):
    """`hidepid` makes ancestors of other users unreadable; stop, don't raise."""
    from IPython.core import kitty

    monkeypatch.setattr(os, "getppid", lambda: 42)
    monkeypatch.setattr(kitty, "_read_proc_stat", _fake_proc({42: ("bash", 7)}))
    assert list(kitty._proc_ancestor_names()) == ["bash"]


def test_supports_kitty_graphics_finds_terminal_through_proc(monkeypatch):
    from IPython.core import kitty

    monkeypatch.delenv("IPYTHON_KITTY_GRAPHICS", raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "stdout", StdoutTTY())
    monkeypatch.setattr(os.path, "isdir", lambda path: path == "/proc/self")
    monkeypatch.setattr(os, "getppid", lambda: 42)
    monkeypatch.setattr(
        kitty,
        "_read_proc_stat",
        _fake_proc({42: ("bash", 7), 7: ("ghostty", 1), 1: ("init", 0)}),
    )
    assert kitty._supports_kitty_graphics() is True


@pytest.mark.skipif(
    not os.path.isdir("/proc/self"),
    reason="the psutil-free walk is the /proc one, and needs a real /proc",
)
def test_supports_kitty_graphics_does_not_import_psutil_on_linux():
    """The /proc walk exists to keep psutil -- and its import cost -- out.

    Deliberately not faking anything about the platform: what is being checked
    is that a real Linux with a real ``/proc`` answers without psutil.
    """
    code = """
import os, sys, builtins

real_import = builtins.__import__

def no_psutil(name, *args, **kwargs):
    assert name != "psutil", "psutil must not be imported by kitty detection"
    return real_import(name, *args, **kwargs)

builtins.__import__ = no_psutil


class StdoutTTY:
    def write(self, *args, **kwargs):
        pass

    def flush(self):
        pass

    def isatty(self):
        return True


sys.stdout = StdoutTTY()
from IPython.core import kitty

kitty._supports_kitty_graphics()
assert "psutil" not in sys.modules
"""
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("IPYTHON_KITTY_GRAPHICS", None)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
