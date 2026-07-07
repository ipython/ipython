# coding: utf-8
"""Tests for IPython.core.application"""

import os
import sys
import tempfile

from tempfile import TemporaryDirectory

import pytest
from traitlets import Unicode
from traitlets.config import Config

from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.testing import decorators as dec


@pytest.fixture
def preserve_excepthook():
    """initialize() installs a crash handler; restore sys.excepthook afterwards."""
    orig = sys.excepthook
    yield
    sys.excepthook = orig


def _clear_singletons(app):
    """Unregister singleton instances created by the subcommand machinery."""
    from traitlets.config.configurable import SingletonConfigurable

    while app is not None:
        for klass in type(app).__mro__:
            if klass is SingletonConfigurable:
                break
            if getattr(klass, "_instance", None) is app:
                klass._instance = None
        app = getattr(app, "subapp", None)


@dec.onlyif_unicode_paths
def test_unicode_cwd():
    """Check that IPython starts with non-ascii characters in the path."""
    wd = tempfile.mkdtemp(suffix="€")

    old_wd = os.getcwd()
    os.chdir(wd)
    # raise Exception(repr(os.getcwd()))
    try:
        app = BaseIPythonApplication()
        # The lines below are copied from Application.initialize()
        app.init_profile_dir()
        app.init_config_files()
        app.load_config_file(suppress_errors=False)
    finally:
        os.chdir(old_wd)


@dec.onlyif_unicode_paths
def test_unicode_ipdir():
    """Check that IPython starts with non-ascii characters in the IP dir."""
    ipdir = tempfile.mkdtemp(suffix="€")

    # Create the config file, so it tries to load it.
    with open(os.path.join(ipdir, "ipython_config.py"), "w", encoding="utf-8") as f:
        pass

    old_ipdir1 = os.environ.pop("IPYTHONDIR", None)
    old_ipdir2 = os.environ.pop("IPYTHON_DIR", None)
    os.environ["IPYTHONDIR"] = ipdir
    try:
        app = BaseIPythonApplication()
        # The lines below are copied from Application.initialize()
        app.init_profile_dir()
        app.init_config_files()
        app.load_config_file(suppress_errors=False)
    finally:
        if old_ipdir1:
            os.environ["IPYTHONDIR"] = old_ipdir1
        if old_ipdir2:
            os.environ["IPYTHONDIR"] = old_ipdir2


def test_cli_priority():
    with TemporaryDirectory() as td:

        class TestApp(BaseIPythonApplication):
            test = Unicode().tag(config=True)

        # Create the config file, so it tries to load it.
        with open(os.path.join(td, "ipython_config.py"), "w", encoding="utf-8") as f:
            f.write("c.TestApp.test = 'config file'")

        app = TestApp()
        app.initialize(["--profile-dir", td])
        assert app.test == "config file"
        app = TestApp()
        app.initialize(["--profile-dir", td, "--TestApp.test=cli"])
        assert app.test == "cli"


def test_extra_config_file(tmp_path, preserve_excepthook):
    """--config loads an extra config file on top of the profile config."""

    class ConfApp(BaseIPythonApplication):
        test = Unicode().tag(config=True)

    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    extra = tmp_path / "extra_config.py"
    extra.write_text("c.ConfApp.test = 'extra'", encoding="utf-8")

    app = ConfApp()
    app.initialize(["--profile-dir", str(profile_dir), "--config", str(extra)])
    assert app.extra_config_file == str(extra)
    assert str(extra) in app.config_files
    assert app.test == "extra"


def test_extra_config_file_missing(tmp_path, preserve_excepthook):
    """A missing --config file is only warned about, not fatal."""
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    missing = tmp_path / "nonexistent_config.py"
    app = BaseIPythonApplication()
    app.initialize(["--profile-dir", str(profile_dir), "--config", str(missing)])
    assert app.extra_config_file == str(missing)


def test_bad_config_file(tmp_path, preserve_excepthook):
    """Errors in config files are suppressed or raised per suppress_errors."""
    from traitlets.config import Application

    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    bad = tmp_path / "bad_config.py"
    bad.write_text("1/0", encoding="utf-8")

    app = BaseIPythonApplication()
    # by default, errors in config files are logged, not raised
    app.initialize(["--profile-dir", str(profile_dir), "--config", str(bad)])
    # make the underlying traitlets loader raise, to exercise IPython's
    # suppress_errors handling
    app.raise_config_file_errors = True
    orig = Application.raise_config_file_errors
    try:
        # suppressed: only a warning is logged
        app.load_config_file(suppress_errors=True)
        # not suppressed: the error propagates
        with pytest.raises(ZeroDivisionError):
            app.load_config_file(suppress_errors=False)
    finally:
        # load_config_file toggles the class-level attribute and cannot
        # restore it when the error propagates
        Application.raise_config_file_errors = orig


def test_config_file_name_changed():
    app = BaseIPythonApplication()
    app.config_file_name = "other_config.py"
    assert "other_config.py" in app.config_file_specified


def test_profile_dir_autocreate_by_name(tmp_path, monkeypatch):
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))
    app = BaseIPythonApplication(profile="fresh", auto_create=True)
    app.init_profile_dir()
    assert (tmp_path / "profile_fresh").is_dir()
    assert app.profile_dir.location == str(tmp_path / "profile_fresh")


def test_profile_not_found_by_name(tmp_path, monkeypatch):
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))
    app = BaseIPythonApplication(profile="nope")
    with pytest.raises(SystemExit):
        app.init_profile_dir()


def test_profile_dir_lazy_default(tmp_path, monkeypatch):
    """Accessing profile_dir forces profile dir initialization."""
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))
    app = BaseIPythonApplication()
    assert app.profile_dir.location == str(tmp_path / "profile_default")
    # a second call is a no-op
    app.init_profile_dir()
    assert app.profile_dir.location == str(tmp_path / "profile_default")


def test_profile_create_by_name_fails(tmp_path, monkeypatch):
    """exit(1) if the profile dir cannot be created."""
    from IPython.core.profiledir import ProfileDirError

    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))

    def raise_profile_dir_error(*args, **kwargs):
        raise ProfileDirError("cannot create")

    monkeypatch.setattr(
        ProfileDir, "create_profile_dir_by_name", raise_profile_dir_error
    )
    app = BaseIPythonApplication(profile="fresh", auto_create=True)
    with pytest.raises(SystemExit):
        app.init_profile_dir()


def test_profile_create_by_location_fails(tmp_path, monkeypatch):
    """exit(1) if the profile dir at an explicit location cannot be created."""
    from IPython.core.profiledir import ProfileDirError

    def raise_profile_dir_error(*args, **kwargs):
        raise ProfileDirError("cannot create")

    monkeypatch.setattr(ProfileDir, "create_profile_dir", raise_profile_dir_error)
    cfg = Config()
    cfg.ProfileDir.location = str(tmp_path / "profile_xyz")
    app = BaseIPythonApplication(config=cfg, auto_create=True)
    with pytest.raises(SystemExit):
        app.init_profile_dir()


def test_copy_config_files_from_builtin(tmp_path, monkeypatch):
    """copy_config_files stages an existing builtin config file."""
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "ip"))
    builtin = tmp_path / "builtin"
    builtin.mkdir()
    (builtin / "ipython_config.py").write_text("# builtin config\n", encoding="utf-8")

    app = BaseIPythonApplication(copy_config_files=True)
    app.builtin_profile_dir = str(builtin)
    app.init_profile_dir()
    app.init_config_files()
    staged = tmp_path / "ip" / "profile_default" / "ipython_config.py"
    assert staged.read_text(encoding="utf-8") == "# builtin config\n"


def test_stage_bundled_config_files(tmp_path, monkeypatch):
    """bundled config files are staged even without copy_config_files."""
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "ip"))
    builtin = tmp_path / "builtin"
    builtin.mkdir()
    (builtin / "extra_bundled.py").write_text("# bundled\n", encoding="utf-8")

    app = BaseIPythonApplication()
    app.builtin_profile_dir = str(builtin)
    app.init_profile_dir()
    app.init_config_files()
    staged = tmp_path / "ip" / "profile_default" / "extra_bundled.py"
    assert staged.read_text(encoding="utf-8") == "# bundled\n"


def test_profile_dir_autocreate_by_location(tmp_path):
    location = tmp_path / "profile_xyz"
    cfg = Config()
    cfg.ProfileDir.location = str(location)
    app = BaseIPythonApplication(config=cfg, auto_create=True)
    app.init_profile_dir()
    assert location.is_dir()
    # profile name is derived from the directory name
    assert app.profile == "xyz"


def test_profile_dir_location_not_found(tmp_path):
    cfg = Config()
    cfg.ProfileDir.location = str(tmp_path / "does_not_exist")
    app = BaseIPythonApplication(config=cfg)
    with pytest.raises(SystemExit):
        app.init_profile_dir()


def test_add_ipython_dir_to_sys_path(tmp_path, monkeypatch):
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "default"))
    app = BaseIPythonApplication(add_ipython_dir_to_sys_path=True)
    ipdir = tmp_path / "ipdir"
    try:
        app.ipython_dir = str(ipdir)
        assert os.path.abspath(str(ipdir)) in sys.path
        assert (ipdir / "extensions").is_dir()
        assert (ipdir / "nbextensions").is_dir()

        # changing the dir removes the old entry from sys.path
        ipdir2 = tmp_path / "ipdir2"
        app.ipython_dir = str(ipdir2)
        assert os.path.abspath(str(ipdir)) not in sys.path
        assert os.path.abspath(str(ipdir2)) in sys.path
    finally:
        for d in (tmp_path / "default", ipdir, tmp_path / "ipdir2"):
            try:
                sys.path.remove(os.path.abspath(str(d)))
            except ValueError:
                pass


def test_excepthook_lite(preserve_excepthook, capsys):
    """without verbose_crash, the light crash handler prints a traceback."""
    app = BaseIPythonApplication()
    app.init_crash_handler()
    assert sys.excepthook == app.excepthook
    try:
        raise ValueError("some error message")
    except ValueError:
        app.excepthook(*sys.exc_info())
    err = capsys.readouterr().err
    assert "some error message" in err
    assert "https://github.com/ipython/ipython/issues" in err


def test_excepthook_verbose_crash(tmp_path, monkeypatch, preserve_excepthook, capsys):
    """with verbose_crash, a crash report is written into the ipython dir."""
    monkeypatch.setattr("builtins.input", lambda *args: "")
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))
    app = BaseIPythonApplication(verbose_crash=True)
    app.init_crash_handler()
    try:
        raise ValueError("crashing for the test")
    except ValueError:
        app.excepthook(*sys.exc_info())
    report = tmp_path / "Crash_report_ipython.txt"
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "IPython post-mortem report" in content
    assert "crashing for the test" in content


def test_load_subconfig_profile_aware(tmp_path, monkeypatch, preserve_excepthook):
    """load_subconfig(..., profile='name') loads config from another profile."""
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))

    class SubCfgApp(BaseIPythonApplication):
        test = Unicode().tag(config=True)

    sub = ProfileDir.create_profile_dir_by_name(tmp_path, "sub")
    with open(
        os.path.join(sub.location, "extra_sub.py"), "w", encoding="utf-8"
    ) as f:
        f.write("c.SubCfgApp.test = 'from sub profile'")

    main = ProfileDir.create_profile_dir_by_name(tmp_path, "default")
    with open(
        os.path.join(main.location, "ipython_config.py"), "w", encoding="utf-8"
    ) as f:
        f.write(
            "load_subconfig('extra_sub.py', profile='sub')\n"
            # missing profiles are silently ignored
            "load_subconfig('extra_sub.py', profile='no_such_profile')\n"
        )

    app = SubCfgApp()
    app.initialize([])
    assert app.test == "from sub profile"


def test_initialize_stops_at_subapp(tmp_path, monkeypatch, preserve_excepthook):
    """initialize() stops early when a subcommand takes over."""
    from IPython.terminal.ipapp import TerminalIPythonApp

    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))
    app = TerminalIPythonApp()
    app.initialize(["profile", "list", "--ipython-dir", str(tmp_path)])
    try:
        assert app.subapp is not None
        # profile dir initialization is skipped when a subapp takes over
        assert not (tmp_path / "profile_default").exists()
    finally:
        _clear_singletons(app)


def test_cwd_disappeared(monkeypatch):
    """exit(1) if the current working directory no longer exists."""
    def missing_cwd():
        raise OSError("cwd does not exist")

    monkeypatch.setattr(os, "getcwd", missing_cwd)
    with pytest.raises(SystemExit):
        BaseIPythonApplication()
