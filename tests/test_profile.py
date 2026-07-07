# coding: utf-8
"""Tests for profile-related functions.

Currently only the startup-dir functionality is tested, but more tests should
be added for:

    * ipython profile create
    * ipython profile list
    * ipython profile create --parallel
    * security dir permissions

Authors
-------

* MinRK

"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import shutil
import sys
import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from IPython.core.profileapp import (
    ProfileApp,
    ProfileCreate,
    ProfileList,
    ProfileLocate,
    list_bundled_profiles,
    list_profiles_in,
)
from IPython.core.profiledir import ProfileDir
from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils.process import getoutput

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
TMP_TEST_DIR = Path(tempfile.mkdtemp())
HOME_TEST_DIR = TMP_TEST_DIR / "home_test_dir"
IP_TEST_DIR = HOME_TEST_DIR / ".ipython"

#
# Setup/teardown functions/decorators
#


def setup_module():
    """Setup test environment for the module:

    - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    (Path.cwd() / IP_TEST_DIR).mkdir(parents=True)


def teardown_module():
    """Teardown test environment for the module:

    - Remove dummy home dir tree
    """
    # Note: we remove the parent test dir, which is the root of all test
    # subdirs we may have created.  Use shutil instead of os.removedirs, so
    # that non-empty directories are all recursively removed.
    shutil.rmtree(TMP_TEST_DIR)


# -----------------------------------------------------------------------------
# Test functions
# -----------------------------------------------------------------------------
@pytest.fixture
def profile_startup(tmp_path):
    pd = ProfileDir.create_profile_dir_by_name(IP_TEST_DIR, "test")
    fname = TMP_TEST_DIR / "test.py"
    options = ["--ipython-dir", IP_TEST_DIR, "--profile", "test"]
    yield pd, fname, options
    shutil.rmtree(pd.location)


def test_startup_py(profile_startup):
    pd, fname, options = profile_startup
    with open(Path(pd.startup_dir) / "00-start.py", "w", encoding="utf-8") as f:
        f.write("zzz=123\n")
    with open(fname, "w", encoding="utf-8") as f:
        f.write("print(zzz)\n")
    tt.ipexec_validate(fname, "123", "", options=options)


def test_startup_ipy(profile_startup):
    pd, fname, options = profile_startup
    with open(Path(pd.startup_dir) / "00-start.ipy", "w", encoding="utf-8") as f:
        f.write("%xmode plain\n")
    with open(fname, "w", encoding="utf-8") as f:
        f.write("")
    tt.ipexec_validate(fname, "Exception reporting mode: Plain", "", options=options)


@pytest.mark.skipif(
    sys.implementation.name == "pypy"
    and ((7, 3, 13) < sys.implementation.version < (7, 3, 16)),
    reason="Unicode issues with scandir on PyPy, see https://github.com/pypy/pypy/issues/4860",
)
def test_list_profiles_in():
    # No need to remove these directories and files, as they will get nuked in
    # the module-level teardown.
    td = Path(tempfile.mkdtemp(dir=TMP_TEST_DIR))
    for name in ("profile_foo", "profile_hello", "not_a_profile"):
        Path(td / name).mkdir(parents=True)
    if dec.unicode_paths:
        Path(td / "profile_ünicode").mkdir(parents=True)

    with open(td / "profile_file", "w", encoding="utf-8") as f:
        f.write("I am not a profile directory")
    profiles = list_profiles_in(td)

    # unicode normalization can turn u'ünicode' into u'u\0308nicode',
    # so only check for *nicode, and that creating a ProfileDir from the
    # name remains valid
    found_unicode = False
    for p in list(profiles):
        if p.endswith("nicode"):
            pd = ProfileDir.find_profile_dir_by_name(td, p)
            profiles.remove(p)
            found_unicode = True
            break
    if dec.unicode_paths:
        assert found_unicode is True
    assert set(profiles) == {"foo", "hello"}


def test_list_bundled_profiles():
    # This variable will need to be updated when a new profile gets bundled
    bundled = sorted(list_bundled_profiles())
    assert bundled == []


@pytest.fixture
def preserve_excepthook():
    """initialize() installs a crash handler; restore sys.excepthook afterwards."""
    orig = sys.excepthook
    yield
    sys.excepthook = orig


def test_profile_create_in_process(tmp_path, preserve_excepthook):
    """ProfileCreate stages default config files into a new profile dir."""
    app = ProfileCreate()
    app.initialize(["foo", "--ipython-dir", str(tmp_path)])
    profile_dir = tmp_path / "profile_foo"
    assert profile_dir.is_dir()
    config_file = profile_dir / "ipython_config.py"
    assert config_file.exists()
    assert app.profile == "foo"


def test_profile_create_reset(tmp_path, preserve_excepthook):
    """ProfileCreate --reset restages default config files."""
    app = ProfileCreate()
    app.initialize(["bar", "--ipython-dir", str(tmp_path)])
    config_file = tmp_path / "profile_bar" / "ipython_config.py"
    default_content = config_file.read_text(encoding="utf-8")
    config_file.write_text("# custom configuration\n", encoding="utf-8")

    # without --reset, the customized file is left alone
    app = ProfileCreate()
    app.initialize(["bar", "--ipython-dir", str(tmp_path)])
    assert config_file.read_text(encoding="utf-8") == "# custom configuration\n"

    # with --reset, defaults are staged over it
    app = ProfileCreate()
    app.initialize(["bar", "--reset", "--ipython-dir", str(tmp_path)])
    assert config_file.read_text(encoding="utf-8") == default_content


def test_profile_create_parallel_trait():
    """The parallel trait adds/removes parallel config files."""
    app = ProfileCreate()
    assert "ipcluster_config.py" not in app.config_files
    app.parallel = True
    for cf in (
        "ipcontroller_config.py",
        "ipengine_config.py",
        "ipcluster_config.py",
    ):
        assert cf in app.config_files
    app.parallel = False
    assert "ipcluster_config.py" not in app.config_files


def test_profile_create_import_app_missing():
    """_import_app returns None on unimportable app paths."""
    app = ProfileCreate()
    assert app._import_app("some_nonexistent_module_xyz.SomeApp") is None


def test_profile_create_import_app_error(monkeypatch):
    """_import_app swallows unexpected errors while importing."""
    def boom(name):
        raise ValueError("boom")

    monkeypatch.setattr("IPython.core.profileapp.import_item", boom)
    app = ProfileCreate()
    assert app._import_app("whatever.App") is None


def test_profile_list_app(tmp_path, monkeypatch, capsys):
    """ProfileList prints profiles from the ipython dir and warns about CWD."""
    ipdir = tmp_path / "ipdir"
    ipdir.mkdir()
    (ipdir / "profile_abc").mkdir()
    cwd = tmp_path / "cwd"
    (cwd / "profile_incwd").mkdir(parents=True)
    monkeypatch.chdir(cwd)

    app = ProfileList()
    app.initialize(["--ipython-dir", str(ipdir)])
    app.start()
    out = capsys.readouterr().out
    assert "Available profiles in %s:" % ipdir in out
    assert "abc" in out
    assert "CVE-2022-21699" in out
    assert "ipython --profile=<name>" in out


def test_profile_locate_app(tmp_path, capsys, preserve_excepthook):
    """ProfileLocate prints the path to a named profile."""
    ProfileDir.create_profile_dir_by_name(tmp_path, "loco")
    app = ProfileLocate()
    app.initialize(["loco", "--ipython-dir", str(tmp_path)])
    app.start()
    out = capsys.readouterr().out
    assert out.strip() == str(tmp_path / "profile_loco")


def test_profile_app_no_subcommand(capsys):
    app = ProfileApp()
    app.initialize([])
    with pytest.raises(SystemExit):
        app.start()
    out = capsys.readouterr().out
    assert "No subcommand specified" in out
    assert "create" in out
    assert "list" in out


def test_profile_app_list_subcommand(tmp_path, capsys):
    """ProfileApp delegates to its subcommand."""
    from traitlets.config.configurable import SingletonConfigurable

    (tmp_path / "profile_viasub").mkdir()
    app = ProfileApp()
    app.initialize(["list", "--ipython-dir", str(tmp_path)])
    try:
        app.start()
    finally:
        # unregister the singleton the subcommand machinery created
        for klass in type(app.subapp).__mro__:
            if klass is SingletonConfigurable:
                break
            if getattr(klass, "_instance", None) is app.subapp:
                klass._instance = None
    out = capsys.readouterr().out
    assert "viasub" in out


def test_profile_create_ipython_dir():
    """ipython profile create respects --ipython-dir"""
    with TemporaryDirectory() as td:
        getoutput(
            [
                sys.executable,
                "-m",
                "IPython",
                "profile",
                "create",
                "foo",
                "--ipython-dir=%s" % td,
            ]
        )
        profile_dir = Path(td) / "profile_foo"
        assert Path(profile_dir).exists()
        ipython_config = profile_dir / "ipython_config.py"
        assert Path(ipython_config).exists()
