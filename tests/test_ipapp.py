"""Tests for IPython.terminal.ipapp, exercised in-process.

These tests build real ``TerminalIPythonApp`` instances pointed at the
temporary IPYTHONDIR set up by ``tests/conftest.py``.  Because
``TerminalInteractiveShell`` is a singleton (created by conftest), every app
attaches to the same shell; the ``make_app`` fixture snapshots and restores
the global state the apps mutate.
"""

import logging
import os
import sys

import pytest

from IPython.testing.decorators import skip_win32

from traitlets.config import Config

from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.terminal.ipapp import (
    IPAppCrashHandler,
    LocateIPythonApp,
    TerminalIPythonApp,
    load_default_config,
)

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def make_app(monkeypatch):
    """Return a factory building initialized TerminalIPythonApp instances.

    Restores the shared-shell state (namespace additions, hidden-variable
    table, configurables, sys.path/argv/excepthook) after the test.
    """
    shell = TerminalInteractiveShell.instance()
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", list(sys.argv))
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.delenv("PYTHONSTARTUP", raising=False)
    saved_hidden = dict(shell.user_ns_hidden)
    n_configurables = len(shell.configurables)
    created_vars = set()

    def factory(argv):
        before = set(shell.user_ns)
        app = TerminalIPythonApp()
        try:
            app.initialize(argv=argv)
        finally:
            created_vars.update(set(shell.user_ns) - before)
        return app

    yield factory

    for name in created_vars:
        shell.user_ns.pop(name, None)
    shell.user_ns_hidden.clear()
    shell.user_ns_hidden.update(saved_hidden)
    del shell.configurables[n_configurables:]
    # reset last_execution_succeeded for tests that ran failing code
    shell.run_cell("pass", store_history=False)


# -----------------------------------------------------------------------------
# code/file/module to run
# -----------------------------------------------------------------------------


def test_code_to_run(make_app):
    app = make_app(["--no-banner", "-c", "zzz_ipapp_c = 40 + 2"])
    assert app.something_to_run is True
    assert app.interact is False
    assert app.shell.user_ns["zzz_ipapp_c"] == 42
    # command-line code should *not* be hidden from %who
    assert "zzz_ipapp_c" not in app.shell.user_ns_hidden
    # successful code -> start() returns without exiting
    app.start()


def test_code_to_run_error_exit_code(make_app):
    app = make_app(["--no-banner", "-c", "1/0"])
    with pytest.raises(SystemExit) as excinfo:
        app.start()
    assert excinfo.value.code == 1


def test_file_to_run(tmp_path, make_app, capsys):
    script = tmp_path / "zzz_script.py"
    script.write_text("zzz_ipapp_file = __file__\nprint('file-ran')\n")
    app = make_app(["--no-banner", str(script)])
    assert app.file_to_run == str(script)
    assert app.interact is False
    out, _ = capsys.readouterr()
    assert "file-ran" in out
    # __file__ is set to the script path while it runs
    assert app.shell.user_ns["zzz_ipapp_file"] == str(script)


def test_file_to_run_gets_sys_argv(tmp_path, make_app):
    script = tmp_path / "zzz_argv_script.py"
    script.write_text("import sys\nzzz_ipapp_argv = list(sys.argv)\n")
    app = make_app(["--no-banner", str(script), "arg1", "arg2"])
    assert app.shell.user_ns["zzz_ipapp_argv"] == [str(script), "arg1", "arg2"]


def test_file_to_run_directory(tmp_path, make_app, capsys):
    (tmp_path / "__main__.py").write_text("print('main-ran')\n")
    make_app(["--no-banner", str(tmp_path)])
    out, _ = capsys.readouterr()
    assert "main-ran" in out


def test_missing_file_exits_with_2(make_app):
    with pytest.raises(SystemExit) as excinfo:
        make_app(["--no-banner", "zzz_no_such_file.py"])
    assert excinfo.value.code == 2


def test_file_raising_error_exits_with_1(tmp_path, make_app):
    script = tmp_path / "zzz_boom.py"
    script.write_text("raise RuntimeError('zzz-boom')\n")
    with pytest.raises(SystemExit) as excinfo:
        make_app(["--no-banner", str(script)])
    assert excinfo.value.code == 1


def test_module_to_run(tmp_path, make_app, monkeypatch, capsys):
    (tmp_path / "zzz_ipapp_mod.py").write_text(
        "print('module-ran')\nzzz_ipapp_mod_var = 7\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    app = make_app(["--no-banner", "-m", "zzz_ipapp_mod"])
    assert app.module_to_run == "zzz_ipapp_mod"
    assert app.interact is False
    out, _ = capsys.readouterr()
    assert "module-ran" in out
    # the module namespace is copied into the user namespace
    assert app.shell.user_ns["zzz_ipapp_mod_var"] == 7


def test_force_interact(make_app):
    app = make_app(["--no-banner", "-i", "-c", "zzz_ipapp_forced = 1"])
    assert app.something_to_run is True
    # -i keeps the shell interactive even with code to run
    assert app.interact is True
    assert app.shell.user_ns["zzz_ipapp_forced"] == 1


# -----------------------------------------------------------------------------
# exec_lines / exec_files / startup files
# -----------------------------------------------------------------------------


def test_exec_lines_run_and_are_hidden(make_app):
    app = make_app(
        [
            "--no-banner",
            "--InteractiveShellApp.exec_lines=['zzz_el = 99', 'zzz_el2 = zzz_el + 1']",
        ]
    )
    assert app.shell.user_ns["zzz_el"] == 99
    assert app.shell.user_ns["zzz_el2"] == 100
    # startup code is hidden from %who by default
    assert "zzz_el" in app.shell.user_ns_hidden
    assert "zzz_el2" in app.shell.user_ns_hidden


def test_exec_lines_error_continues(make_app):
    app = make_app(
        ["--no-banner", "--InteractiveShellApp.exec_lines=['1/0', 'zzz_after = 5']"]
    )
    # an error in one line doesn't prevent the next from running
    assert app.shell.user_ns["zzz_after"] == 5


@skip_win32
def test_exec_files(tmp_path, make_app):
    pyfile = tmp_path / "zzz_a.py"
    pyfile.write_text("zzz_exec_py = 1\n")
    ipyfile = tmp_path / "zzz_b.ipy"
    ipyfile.write_text("zzz_exec_ipy = 2\n")
    app = make_app(
        [
            "--no-banner",
            "--InteractiveShellApp.exec_files=['%s', '%s']" % (pyfile, ipyfile),
        ]
    )
    assert app.shell.user_ns["zzz_exec_py"] == 1
    assert app.shell.user_ns["zzz_exec_ipy"] == 2


def test_exec_files_missing_is_only_a_warning(make_app):
    app = make_app(
        ["--no-banner", "--InteractiveShellApp.exec_files=['zzz_no_such_file.py']"]
    )
    # a missing exec_file is not fatal
    assert app.shell is not None


def test_startup_files_and_pythonstartup(tmp_path, make_app, monkeypatch):
    ps = tmp_path / "zzz_pythonstartup.py"
    ps.write_text("zzz_pythonstartup = 'ps'\n")
    monkeypatch.setenv("PYTHONSTARTUP", str(ps))
    startup_dir = os.path.join(os.environ["IPYTHONDIR"], "profile_default", "startup")
    os.makedirs(startup_dir, exist_ok=True)
    startup_file = os.path.join(startup_dir, "zzz_startup.py")
    with open(startup_file, "w") as fh:
        fh.write("zzz_startup_var = 'su'\n")
    try:
        app = make_app(["--no-banner"])
        assert app.shell.user_ns["zzz_pythonstartup"] == "ps"
        assert app.shell.user_ns["zzz_startup_var"] == "su"
    finally:
        os.unlink(startup_file)


def test_startup_file_error_is_not_fatal(tmp_path, make_app, monkeypatch, capsys):
    ps = tmp_path / "zzz_bad_pythonstartup.py"
    ps.write_text("raise ValueError('zzz-bad-pythonstartup')\n")
    monkeypatch.setenv("PYTHONSTARTUP", str(ps))
    startup_dir = os.path.join(os.environ["IPYTHONDIR"], "profile_default", "startup")
    os.makedirs(startup_dir, exist_ok=True)
    startup_file = os.path.join(startup_dir, "zzz_bad_startup.py")
    with open(startup_file, "w") as fh:
        fh.write("raise ValueError('zzz-bad-startup')\n")
    try:
        app = make_app(["--no-banner"])
        assert app.shell is not None
        out, err = capsys.readouterr()
        assert "zzz-bad-pythonstartup" in out + err
        assert "zzz-bad-startup" in out + err
    finally:
        os.unlink(startup_file)


@skip_win32
def test_exec_files_error_is_not_fatal(tmp_path, make_app, capsys):
    bad = tmp_path / "zzz_bad_exec.py"
    bad.write_text("raise ValueError('zzz-bad-exec-file')\n")
    app = make_app(
        ["--no-banner", "--InteractiveShellApp.exec_files=['%s']" % bad]
    )
    assert app.shell is not None
    out, err = capsys.readouterr()
    assert "zzz-bad-exec-file" in out + err


# -----------------------------------------------------------------------------
# extensions
# -----------------------------------------------------------------------------


def test_missing_extension_is_only_a_warning(make_app):
    app = make_app(["--no-banner", "--ext", "zzz_no_such_extension"])
    assert app.shell is not None


def test_missing_extension_reraise(make_app):
    with pytest.raises(ModuleNotFoundError):
        make_app(
            [
                "--no-banner",
                "--ext",
                "zzz_no_such_extension",
                "--InteractiveShellApp.reraise_ipython_extension_failures=True",
            ]
        )


# -----------------------------------------------------------------------------
# banner / flags / subcommands
# -----------------------------------------------------------------------------


def test_banner_displayed(make_app, capsys):
    app = make_app(["--banner", "--log-level=%d" % logging.INFO])
    assert app.interact is True
    out, _ = capsys.readouterr()
    assert "IPython" in out


def test_no_banner(make_app, capsys):
    make_app(["--no-banner"])
    out, _ = capsys.readouterr()
    assert "An enhanced Interactive Python" not in out


def test_quick_flag_skips_config_files(make_app):
    app = make_app(["--quick", "--no-banner"])
    assert app.quick is True
    # load_config_file has been replaced by a no-op
    assert app.load_config_file(suppress_errors=True) is None


def test_locate_subcommand(make_app, capsys):
    app = make_app(["locate"])
    assert app.subapp is not None
    app.start()
    out, _ = capsys.readouterr()
    assert os.environ["IPYTHONDIR"] in out


def test_locate_app_direct(monkeypatch, capsys):
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    app = LocateIPythonApp()
    app.initialize([])
    app.start()
    out, _ = capsys.readouterr()
    assert os.environ["IPYTHONDIR"] in out


def test_locate_profile_subcommand(monkeypatch, capsys):
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    app = LocateIPythonApp()
    app.initialize(["profile"])
    assert app.subapp is not None
    app.start()
    out, _ = capsys.readouterr()
    assert "profile_default" in out


# -----------------------------------------------------------------------------
# gui / matplotlib / pylab initialization
# -----------------------------------------------------------------------------


def test_init_gui_pylab_gui(make_app, monkeypatch):
    app = make_app(["--no-banner"])
    calls = []
    monkeypatch.setattr(app.shell, "enable_gui", lambda key=None: calls.append(key) or "qt")
    app.gui = "qt"
    app.init_gui_pylab()
    assert calls == ["qt"]


def test_init_gui_pylab_matplotlib_auto(make_app, monkeypatch, capsys):
    pytest.importorskip("matplotlib")
    app = make_app(["--no-banner"])
    monkeypatch.setattr(app.shell, "enable_matplotlib", lambda key: ("qt", "qtagg"))
    app.matplotlib = "auto"
    app.init_gui_pylab()
    out, _ = capsys.readouterr()
    # with --matplotlib=auto the chosen backend is printed
    assert "Using matplotlib backend: qtagg" in out


def test_init_gui_pylab_pylab(make_app, monkeypatch):
    pytest.importorskip("matplotlib")
    app = make_app(["--no-banner"])
    calls = {}

    def fake_enable_pylab(key, import_all=None):
        calls["key"] = key
        calls["import_all"] = import_all
        return ("qt", "qtagg")

    monkeypatch.setattr(app.shell, "enable_pylab", fake_enable_pylab)
    app.pylab = "qt"
    app.init_gui_pylab()
    assert calls == {"key": "qt", "import_all": True}


def test_init_gui_pylab_import_error(make_app, monkeypatch, capsys):
    app = make_app(["--no-banner"])

    def raise_import_error(key=None):
        raise ImportError("zzz-no-matplotlib")

    monkeypatch.setattr(app.shell, "enable_gui", raise_import_error)
    app.gui = "qt"
    # failure to enable the event loop is not fatal
    app.init_gui_pylab()
    out, err = capsys.readouterr()
    assert "zzz-no-matplotlib" in out + err


def test_init_gui_pylab_other_error(make_app, monkeypatch, capsys):
    app = make_app(["--no-banner"])

    def raise_runtime_error(key=None):
        raise RuntimeError("zzz-gui-boom")

    monkeypatch.setattr(app.shell, "enable_gui", raise_runtime_error)
    app.gui = "qt"
    app.init_gui_pylab()
    out, err = capsys.readouterr()
    assert "zzz-gui-boom" in out + err


def test_pylab_inline_replaced_by_auto(make_app):
    pytest.importorskip("matplotlib")
    app = make_app(["--no-banner"])
    with pytest.warns(UserWarning, match="'inline' not available"):
        app._pylab_changed("pylab", None, "inline")
    assert app.pylab == "auto"


# -----------------------------------------------------------------------------
# misc: crash handler, load_default_config
# -----------------------------------------------------------------------------


def test_crash_handler_report(make_app):
    app = make_app(["--no-banner", "-c", "zzz_ipapp_crash = 1"])
    handler = IPAppCrashHandler(app)
    report = handler.make_report("fake traceback")
    assert "IPython post-mortem report" in report
    assert "History of session input" in report


def test_crash_handler_report_without_shell():
    # an app without an initialized shell still produces a report
    app = TerminalIPythonApp()
    handler = IPAppCrashHandler(app)
    report = handler.make_report("fake traceback")
    assert "IPython post-mortem report" in report


def test_load_default_config(tmp_path):
    profile = tmp_path / "profile_default"
    profile.mkdir()
    (profile / "ipython_config.py").write_text(
        "c.TerminalIPythonApp.display_banner = False\n"
    )
    config = load_default_config(str(tmp_path))
    assert config.TerminalIPythonApp.display_banner is False


def test_load_default_config_default_dir():
    # with no argument, the IPYTHONDIR environment variable is used
    config = load_default_config()
    assert isinstance(config, Config)
