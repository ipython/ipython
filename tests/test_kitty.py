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
