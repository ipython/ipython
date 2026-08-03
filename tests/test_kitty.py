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
    import platform

    from IPython.core import kitty

    monkeypatch.setattr(platform, "system", lambda: "Linux")
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
    import platform

    import psutil

    from IPython.core import kitty

    monkeypatch.setattr(platform, "system", lambda: "Linux")
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
