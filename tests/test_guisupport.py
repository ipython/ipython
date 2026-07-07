"""Tests for IPython.lib.guisupport.

These tests use fake toolkit modules/objects injected into ``sys.modules`` so
that no real GUI toolkit (wx, Qt) is imported or started.
"""

import sys
import types

import pytest

from IPython.lib import guisupport

# -----------------------------------------------------------------------------
# Fakes
# -----------------------------------------------------------------------------


class FakeWxApp:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.main_loop_calls = 0
        self.main_loop_running = False

    def MainLoop(self):
        self.main_loop_calls += 1

    def IsMainLoopRunning(self):
        return self.main_loop_running


def make_fake_wx(existing_app=None):
    """Build a fake ``wx`` module whose GetApp() returns *existing_app*."""
    wx = types.ModuleType("wx")
    wx.GetApp = lambda: existing_app
    wx.PySimpleApp = FakeWxApp
    return wx


class FakeQtApp:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.exec_calls = 0

    def exec_(self):
        self.exec_calls += 1


def make_fake_qt(existing_app=None, monkeypatch=None):
    """Build a fake ``IPython.external.qt_for_kernel`` module."""

    class FakeQApplication(FakeQtApp):
        @staticmethod
        def instance():
            return existing_app

    qt_mod = types.ModuleType("IPython.external.qt_for_kernel")
    qt_mod.QtGui = types.SimpleNamespace(QApplication=FakeQApplication)
    monkeypatch.setitem(sys.modules, "IPython.external.qt_for_kernel", qt_mod)
    return FakeQApplication


class FakeShell:
    def __init__(self, active_eventloop=None):
        self.active_eventloop = active_eventloop


@pytest.fixture
def no_ipython(monkeypatch):
    """Make guisupport believe no IPython shell is active."""
    monkeypatch.setattr(guisupport, "get_ipython", lambda: None)


# -----------------------------------------------------------------------------
# wx
# -----------------------------------------------------------------------------


def test_get_app_wx_creates_new_app(monkeypatch):
    monkeypatch.setitem(sys.modules, "wx", make_fake_wx(existing_app=None))
    app = guisupport.get_app_wx()
    assert isinstance(app, FakeWxApp)
    # redirect=False is filled in by default
    assert app.kwargs == {"redirect": False}


def test_get_app_wx_keeps_explicit_redirect(monkeypatch):
    monkeypatch.setitem(sys.modules, "wx", make_fake_wx(existing_app=None))
    app = guisupport.get_app_wx(redirect=True)
    assert app.kwargs == {"redirect": True}


def test_get_app_wx_returns_existing_app(monkeypatch):
    existing = FakeWxApp()
    monkeypatch.setitem(sys.modules, "wx", make_fake_wx(existing_app=existing))
    assert guisupport.get_app_wx() is existing


def test_is_event_loop_running_wx_active_eventloop(monkeypatch):
    monkeypatch.setattr(guisupport, "get_ipython", lambda: FakeShell("wx"))
    assert guisupport.is_event_loop_running_wx() is True


def test_is_event_loop_running_wx_in_event_loop_attribute(no_ipython):
    app = FakeWxApp()
    app._in_event_loop = True
    assert guisupport.is_event_loop_running_wx(app) is True
    app._in_event_loop = False
    assert guisupport.is_event_loop_running_wx(app) is False


def test_is_event_loop_running_wx_queries_toolkit(no_ipython):
    # Without the _in_event_loop attribute, fall back to wx's own check.
    app = FakeWxApp()
    app.main_loop_running = True
    assert guisupport.is_event_loop_running_wx(app) is True
    app.main_loop_running = False
    assert guisupport.is_event_loop_running_wx(app) is False


def test_is_event_loop_running_wx_falls_through_for_other_eventloop(monkeypatch):
    # An active non-wx eventloop must not count as a running wx loop.
    monkeypatch.setattr(guisupport, "get_ipython", lambda: FakeShell("qt"))
    app = FakeWxApp()
    app._in_event_loop = False
    assert guisupport.is_event_loop_running_wx(app) is False


def test_is_event_loop_running_wx_default_app(no_ipython, monkeypatch):
    existing = FakeWxApp()
    existing._in_event_loop = True
    monkeypatch.setitem(sys.modules, "wx", make_fake_wx(existing_app=existing))
    assert guisupport.is_event_loop_running_wx() is True


def test_start_event_loop_wx_runs_main_loop(no_ipython):
    app = FakeWxApp()
    guisupport.start_event_loop_wx(app)
    assert app.main_loop_calls == 1
    # The informal protocol: flag is reset once MainLoop returns.
    assert app._in_event_loop is False


def test_start_event_loop_wx_already_running(no_ipython):
    app = FakeWxApp()
    app._in_event_loop = True
    guisupport.start_event_loop_wx(app)
    assert app.main_loop_calls == 0
    assert app._in_event_loop is True


def test_start_event_loop_wx_default_app(no_ipython, monkeypatch):
    existing = FakeWxApp()
    monkeypatch.setitem(sys.modules, "wx", make_fake_wx(existing_app=existing))
    guisupport.start_event_loop_wx()
    assert existing.main_loop_calls == 1
    assert existing._in_event_loop is False


# -----------------------------------------------------------------------------
# qt4
# -----------------------------------------------------------------------------


def test_get_app_qt4_creates_new_app(monkeypatch):
    FakeQApplication = make_fake_qt(existing_app=None, monkeypatch=monkeypatch)
    app = guisupport.get_app_qt4()
    assert isinstance(app, FakeQApplication)
    # Default argv is a single empty string.
    assert app.args == ([""],)


def test_get_app_qt4_custom_args(monkeypatch):
    make_fake_qt(existing_app=None, monkeypatch=monkeypatch)
    app = guisupport.get_app_qt4(["myprog"])
    assert app.args == (["myprog"],)


def test_get_app_qt4_returns_existing_app(monkeypatch):
    existing = FakeQtApp()
    make_fake_qt(existing_app=existing, monkeypatch=monkeypatch)
    assert guisupport.get_app_qt4() is existing


def test_is_event_loop_running_qt4_active_eventloop(monkeypatch):
    monkeypatch.setattr(guisupport, "get_ipython", lambda: FakeShell("qt6"))
    assert guisupport.is_event_loop_running_qt4() is True
    monkeypatch.setattr(guisupport, "get_ipython", lambda: FakeShell("wx"))
    assert guisupport.is_event_loop_running_qt4() is False
    # No active eventloop on the shell -> falsy result
    monkeypatch.setattr(guisupport, "get_ipython", lambda: FakeShell(None))
    assert not guisupport.is_event_loop_running_qt4()


def test_is_event_loop_running_qt4_in_event_loop_attribute(no_ipython):
    app = FakeQtApp()
    app._in_event_loop = True
    assert guisupport.is_event_loop_running_qt4(app) is True
    app._in_event_loop = False
    assert guisupport.is_event_loop_running_qt4(app) is False


def test_is_event_loop_running_qt4_no_attribute(no_ipython):
    # Qt has no native way to check, so this is False.
    assert guisupport.is_event_loop_running_qt4(FakeQtApp()) is False


def test_is_event_loop_running_qt4_default_app(no_ipython, monkeypatch):
    existing = FakeQtApp()
    existing._in_event_loop = True
    make_fake_qt(existing_app=existing, monkeypatch=monkeypatch)
    assert guisupport.is_event_loop_running_qt4() is True


def test_start_event_loop_qt4_runs_exec(no_ipython):
    app = FakeQtApp()
    guisupport.start_event_loop_qt4(app)
    assert app.exec_calls == 1
    assert app._in_event_loop is False


def test_start_event_loop_qt4_already_running(no_ipython):
    app = FakeQtApp()
    app._in_event_loop = True
    guisupport.start_event_loop_qt4(app)
    assert app.exec_calls == 0
    assert app._in_event_loop is True


def test_start_event_loop_qt4_default_app(no_ipython, monkeypatch):
    existing = FakeQtApp()
    make_fake_qt(existing_app=existing, monkeypatch=monkeypatch)
    guisupport.start_event_loop_qt4()
    assert existing.exec_calls == 1
    assert existing._in_event_loop is False
