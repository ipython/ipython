"""Tests for IPython.core.crashhandler"""

import sys
from unittest.mock import MagicMock

import pytest

from IPython.core import crashhandler
from IPython.core.crashhandler import CrashHandler, crash_handler_lite
from IPython.core.interactiveshell import InteractiveShell


class FakeApp:
    """Minimal stand-in for an IPython Application."""

    name = "testapp"

    def __init__(self, ipython_dir=None):
        if ipython_dir is not None:
            self.ipython_dir = ipython_dir
        self.config = {"FakeApp": {"answer": 42}}


def _exc_info():
    try:
        raise ValueError("crash-handler-test")
    except ValueError:
        return sys.exc_info()


@pytest.fixture
def input_prompts(monkeypatch):
    """Replace builtins.input, recording the prompts it was called with."""
    prompts = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


@pytest.fixture(autouse=True)
def restore_excepthook(monkeypatch):
    # CrashHandler.__call__ resets sys.excepthook; make sure this does not
    # leak out of the tests.
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)


def test_crash_handler_init():
    app = FakeApp()
    ch = CrashHandler(
        app,
        contact_name="Jane Dev",
        contact_email="jane@example.com",
        bug_tracker="https://example.com/bugs",
    )
    assert ch.crash_report_fname == "Crash_report_testapp.txt"
    assert ch.app is app
    assert ch.call_pdb is False
    assert ch.show_crash_traceback is True
    assert ch.info["app_name"] == "testapp"
    assert ch.info["contact_name"] == "Jane Dev"
    assert ch.info["contact_email"] == "jane@example.com"
    assert ch.info["bug_tracker"] == "https://example.com/bugs"
    assert ch.info["crash_report_fname"] == "Crash_report_testapp.txt"


def test_crash_handler_writes_report(tmp_path, capsys, input_prompts):
    app = FakeApp(ipython_dir=str(tmp_path))
    ch = CrashHandler(
        app,
        contact_name="Jane Dev",
        contact_email="jane@example.com",
        bug_tracker="https://example.com/bugs",
    )
    etype, evalue, etb = _exc_info()
    ch(etype, evalue, etb)

    report_file = tmp_path / "Crash_report_testapp.txt"
    assert report_file.is_file()
    text = report_file.read_text(encoding="utf-8")
    assert "IPython post-mortem report" in text
    assert "Application name: testapp" in text
    assert "Crash traceback:" in text
    assert "ValueError" in text
    assert "crash-handler-test" in text

    err = capsys.readouterr().err
    # user-facing message
    assert "Oops, testapp crashed." in err
    assert "jane@example.com" in err
    assert str(report_file) in err
    # traceback shown on stderr by default
    assert "ValueError" in err

    # the filename was expanded to the full path
    assert ch.crash_report_fname == str(report_file)
    assert ch.info["crash_report_fname"] == str(report_file)
    # the crash handler uninstalls itself
    assert sys.excepthook is sys.__excepthook__
    # and waits for the user to acknowledge
    assert len(input_prompts) == 1


def test_crash_handler_hidden_traceback(tmp_path, capsys, input_prompts):
    app = FakeApp(ipython_dir=str(tmp_path))
    ch = CrashHandler(app, show_crash_traceback=False)
    etype, evalue, etb = _exc_info()
    ch(etype, evalue, etb)

    err = capsys.readouterr().err
    # message is still printed, but not the traceback
    assert "Oops, testapp crashed." in err
    assert "ValueError" not in err
    # the report on disk still has the traceback
    text = (tmp_path / "Crash_report_testapp.txt").read_text(encoding="utf-8")
    assert "ValueError" in text


def test_crash_handler_no_ipython_dir(tmp_path, monkeypatch, capsys, input_prompts):
    # app without an ipython_dir attribute: report goes to cwd
    monkeypatch.chdir(tmp_path)
    ch = CrashHandler(FakeApp())
    etype, evalue, etb = _exc_info()
    ch(etype, evalue, etb)
    assert (tmp_path / "Crash_report_testapp.txt").is_file()
    capsys.readouterr()


def test_crash_handler_missing_ipython_dir(tmp_path, monkeypatch, capsys, input_prompts):
    # nonexistent ipython_dir: falls back to cwd
    monkeypatch.chdir(tmp_path)
    ch = CrashHandler(FakeApp(ipython_dir=str(tmp_path / "does-not-exist")))
    etype, evalue, etb = _exc_info()
    ch(etype, evalue, etb)
    assert (tmp_path / "Crash_report_testapp.txt").is_file()
    capsys.readouterr()


def test_crash_handler_unwritable_report(tmp_path, capsys, input_prompts):
    # make open() fail by occupying the report path with a directory
    (tmp_path / "Crash_report_testapp.txt").mkdir()
    ch = CrashHandler(FakeApp(ipython_dir=str(tmp_path)))
    etype, evalue, etb = _exc_info()
    ch(etype, evalue, etb)

    err = capsys.readouterr().err
    assert "Could not create crash report on disk." in err
    # bails out before the user message and the input() prompt
    assert "Oops, testapp crashed." not in err
    assert input_prompts == []


def test_crash_handler_call_pdb(tmp_path, monkeypatch, input_prompts):
    tb_instance = MagicMock()
    verbose_tb = MagicMock(return_value=tb_instance)
    monkeypatch.setattr(crashhandler.ultratb, "VerboseTB", verbose_tb)

    ch = CrashHandler(FakeApp(ipython_dir=str(tmp_path)), call_pdb=True)
    etype, evalue, etb = _exc_info()
    ch(etype, evalue, etb)

    verbose_tb.assert_called_once_with(
        theme_name="nocolor", long_header=True, call_pdb=True
    )
    tb_instance.assert_called_once_with(etype, evalue, etb)
    # with call_pdb, no report is written and input() is not called
    assert not (tmp_path / "Crash_report_testapp.txt").exists()
    assert input_prompts == []


def test_make_report_contains_config():
    ch = CrashHandler(FakeApp())
    report = ch.make_report("FAKE TRACEBACK")
    assert "IPython post-mortem report" in report
    assert "Application name: testapp" in report
    assert "Current user configuration structure:" in report
    assert "'answer': 42" in report
    assert report.endswith("Crash traceback:\n\nFAKE TRACEBACK")


def test_make_report_without_config():
    app = FakeApp()
    del app.config
    ch = CrashHandler(app)
    report = ch.make_report("FAKE TRACEBACK")
    # the config section is skipped, the rest is still there
    assert "IPython post-mortem report" in report
    assert "Application name" not in report
    assert "FAKE TRACEBACK" in report


def test_crash_handler_lite_no_shell(capsys, monkeypatch):
    monkeypatch.setattr(InteractiveShell, "initialized", lambda: False)
    etype, evalue, etb = _exc_info()
    crash_handler_lite(etype, evalue, etb)
    err = capsys.readouterr().err
    assert "ValueError: crash-handler-test" in err
    assert "If you suspect this is an IPython" in err
    # outside of a shell, generic config syntax is suggested
    assert "c.Application.verbose_crash=True" in err


def test_crash_handler_lite_in_shell(capsys, monkeypatch):
    monkeypatch.setattr(InteractiveShell, "initialized", lambda: True)
    etype, evalue, etb = _exc_info()
    crash_handler_lite(etype, evalue, etb)
    err = capsys.readouterr().err
    assert "ValueError: crash-handler-test" in err
    # inside a shell, the %config magic is suggested
    assert "%config Application.verbose_crash=True" in err
