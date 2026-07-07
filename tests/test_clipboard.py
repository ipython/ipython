import subprocess
import sys
import types

import pytest

from IPython.core.error import TryNext
from IPython.lib import clipboard
from IPython.lib.clipboard import (
    ClipboardEmpty,
    osx_clipboard_get,
    tkinter_clipboard_get,
    wayland_clipboard_get,
    win32_clipboard_get,
)
from IPython.testing.decorators import skip_if_no_x11


@skip_if_no_x11
def test_clipboard_get():
    # Smoketest for clipboard access - we can't easily guarantee that the
    # clipboard is accessible and has something on it, but this tries to
    # exercise the relevant code anyway.
    try:
        a = get_ipython().hooks.clipboard_get()
    except ClipboardEmpty:
        # Nothing in clipboard to get
        pass
    except TryNext:
        # No clipboard access API available
        pass
    else:
        assert isinstance(a, str)


class FakePopen:
    """Minimal stand-in for subprocess.Popen usable as a context manager."""

    calls = []

    def __init__(self, cmd, stdout=None):
        type(self).calls.append(cmd)
        self.returncode = 0

    def communicate(self, input=None):
        return (b"", b"")

    def wait(self):
        return self.returncode

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.fixture
def popen_recorder(monkeypatch):
    """Install a FakePopen subclass in place of subprocess.Popen."""

    def install(output=b"", returncode=0):
        class Recorder(FakePopen):
            calls = []

            def __init__(self, cmd, stdout=None):
                super().__init__(cmd, stdout=stdout)
                self.returncode = returncode

            def communicate(self, input=None):
                return (output, b"")

        monkeypatch.setattr(subprocess, "Popen", Recorder)
        return Recorder

    return install


# -----------------------------------------------------------------------------
# OS X (pbpaste)
# -----------------------------------------------------------------------------


def test_osx_clipboard_get(popen_recorder):
    recorder = popen_recorder(output=b"old\rmac\rline endings")
    text = osx_clipboard_get()
    # \r line endings are normalized to \n and bytes decoded to str
    assert text == "old\nmac\nline endings"
    assert recorder.calls == [["pbpaste", "-Prefer", "ascii"]]


# -----------------------------------------------------------------------------
# Wayland (wl-paste)
# -----------------------------------------------------------------------------


def test_wayland_clipboard_get(monkeypatch, popen_recorder):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    recorder = popen_recorder(output=b"wayland text")
    assert wayland_clipboard_get() == "wayland text"
    assert recorder.calls == [["wl-paste"]]


def test_wayland_clipboard_not_wayland(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    with pytest.raises(TryNext, match="wayland is not detected"):
        wayland_clipboard_get()


def test_wayland_clipboard_no_wl_paste(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")

    def raise_fnf(*args, **kwargs):
        raise FileNotFoundError("wl-paste")

    monkeypatch.setattr(subprocess, "Popen", raise_fnf)
    with pytest.raises(TryNext, match="wl-clipboard"):
        wayland_clipboard_get()


def test_wayland_clipboard_command_failure(monkeypatch, popen_recorder):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    popen_recorder(output=b"whatever", returncode=1)
    with pytest.raises(TryNext):
        wayland_clipboard_get()


def test_wayland_clipboard_empty(monkeypatch, popen_recorder):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    popen_recorder(output=b"")
    with pytest.raises(ClipboardEmpty):
        wayland_clipboard_get()


# -----------------------------------------------------------------------------
# Windows (pywin32)
# -----------------------------------------------------------------------------


def make_fake_win32clipboard(data):
    """Build a fake win32clipboard module.

    *data* maps clipboard formats to either text or an exception to raise.
    """
    mod = types.ModuleType("win32clipboard")

    class error(Exception):
        pass

    mod.error = error
    mod.CF_UNICODETEXT = 13
    mod.CF_TEXT = 1
    mod.opened = False
    mod.closed = False
    mod.data = dict(data)

    def OpenClipboard():
        mod.opened = True

    def CloseClipboard():
        mod.closed = True

    def GetClipboardData(fmt):
        result = mod.data[fmt]
        if isinstance(result, Exception):
            raise result
        return result

    mod.OpenClipboard = OpenClipboard
    mod.CloseClipboard = CloseClipboard
    mod.GetClipboardData = GetClipboardData
    return mod


def test_win32_clipboard_get_unicode(monkeypatch):
    fake = make_fake_win32clipboard({13: "unicode text"})
    monkeypatch.setitem(sys.modules, "win32clipboard", fake)
    assert win32_clipboard_get() == "unicode text"
    assert fake.opened
    assert fake.closed


def test_win32_clipboard_get_fallback_to_cf_text(monkeypatch):
    fake = make_fake_win32clipboard({13: TypeError("no unicode"), 1: b"plain text"})
    monkeypatch.setitem(sys.modules, "win32clipboard", fake)
    assert win32_clipboard_get() == "plain text"
    assert fake.closed


def test_win32_clipboard_get_empty(monkeypatch):
    fake = make_fake_win32clipboard({})
    fake.data.update({13: fake.error("empty"), 1: fake.error("empty")})
    monkeypatch.setitem(sys.modules, "win32clipboard", fake)
    with pytest.raises(ClipboardEmpty):
        win32_clipboard_get()
    # The clipboard must be closed even on failure.
    assert fake.closed


def test_win32_clipboard_get_no_pywin32(monkeypatch):
    monkeypatch.setitem(sys.modules, "win32clipboard", None)
    with pytest.raises(TryNext, match="pywin32"):
        win32_clipboard_get()


# -----------------------------------------------------------------------------
# Tkinter
# -----------------------------------------------------------------------------


def make_fake_tkinter(text=None):
    mod = types.ModuleType("tkinter")

    class TclError(Exception):
        pass

    class Tk:
        instances = []

        def __init__(self):
            type(self).instances.append(self)
            self.withdrawn = False
            self.destroyed = False

        def withdraw(self):
            self.withdrawn = True

        def clipboard_get(self):
            if text is None:
                raise TclError("CLIPBOARD selection doesn't exist")
            return text

        def destroy(self):
            self.destroyed = True

    mod.TclError = TclError
    mod.Tk = Tk
    return mod


def test_tkinter_clipboard_get(monkeypatch):
    fake = make_fake_tkinter(text="tk text")
    monkeypatch.setitem(sys.modules, "tkinter", fake)
    assert tkinter_clipboard_get() == "tk text"
    (root,) = fake.Tk.instances
    assert root.withdrawn
    assert root.destroyed


def test_tkinter_clipboard_get_empty(monkeypatch):
    fake = make_fake_tkinter(text=None)
    monkeypatch.setitem(sys.modules, "tkinter", fake)
    with pytest.raises(ClipboardEmpty):
        tkinter_clipboard_get()
    # The Tk root window is destroyed even when the clipboard is empty.
    (root,) = fake.Tk.instances
    assert root.destroyed


def test_tkinter_clipboard_get_no_tkinter(monkeypatch):
    monkeypatch.setitem(sys.modules, "tkinter", None)
    with pytest.raises(TryNext, match="tkinter"):
        tkinter_clipboard_get()
