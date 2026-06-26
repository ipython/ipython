import subprocess
import sys
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
