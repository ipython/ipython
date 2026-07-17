# encoding: utf-8
"""Tests for IPython.utils.path.py"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from importlib import reload
from os.path import abspath, join
from unittest.mock import patch

import pytest
from tempfile import TemporaryDirectory

import IPython
from IPython import paths
from IPython.testing import decorators as dec
from IPython.testing.decorators import (
    onlyif_unicode_paths,
    skip_if_not_win32,
    skip_win32,
)
from IPython.testing.tools import make_tempfile
from IPython.utils import path

# Platform-dependent imports
try:
    import winreg as wreg
except ImportError:
    # Fake _winreg module on non-windows platforms
    import types

    wr_name = "winreg"
    sys.modules[wr_name] = types.ModuleType(wr_name)
    try:
        import winreg as wreg
    except ImportError:
        import _winreg as wreg

        # Add entries that needs to be stubbed by the testing code
        (
            wreg.OpenKey,
            wreg.QueryValueEx,
        ) = (None, None)

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
env = os.environ
TMP_TEST_DIR = tempfile.mkdtemp()
HOME_TEST_DIR = join(TMP_TEST_DIR, "home_test_dir")
#
# Setup/teardown functions/decorators
#


def setup_module():
    """Setup testenvironment for the module:

    - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    os.makedirs(os.path.join(HOME_TEST_DIR, "ipython"))


def teardown_module():
    """Teardown testenvironment for the module:

    - Remove dummy home dir tree
    """
    # Note: we remove the parent test dir, which is the root of all test
    # subdirs we may have created.  Use shutil instead of os.removedirs, so
    # that non-empty directories are all recursively removed.
    shutil.rmtree(TMP_TEST_DIR)


# Build decorator that uses the setup_environment/setup_environment
@pytest.fixture
def environment():
    global oldstuff, platformstuff
    oldstuff = (
        env.copy(),
        os.name,
        sys.platform,
        path.get_home_dir,
        IPython.__file__,
        os.getcwd(),
    )

    yield

    (
        oldenv,
        os.name,
        sys.platform,
        path.get_home_dir,
        IPython.__file__,
        old_wd,
    ) = oldstuff
    os.chdir(old_wd)
    reload(path)

    for key in list(env):
        if key not in oldenv:
            del env[key]
    env.update(oldenv)
    assert not hasattr(sys, "frozen")


with_environment = pytest.mark.usefixtures("environment")


@skip_if_not_win32
@with_environment
def test_get_home_dir_1(monkeypatch):
    """Testcase for py2exe logic, un-compressed lib"""
    unfrozen = path.get_home_dir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    # fake filename for IPython.__init__
    IPython.__file__ = abspath(join(HOME_TEST_DIR, "Lib/IPython/__init__.py"))

    home_dir = path.get_home_dir()
    assert home_dir == unfrozen


@skip_if_not_win32
@with_environment
def test_get_home_dir_2(monkeypatch):
    """Testcase for py2exe logic, compressed lib"""
    unfrozen = path.get_home_dir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    # fake filename for IPython.__init__
    IPython.__file__ = abspath(
        join(HOME_TEST_DIR, "Library.zip/IPython/__init__.py")
    ).lower()

    home_dir = path.get_home_dir(True)
    assert home_dir == unfrozen


@skip_win32
@with_environment
def test_get_home_dir_3():
    """get_home_dir() uses $HOME if set"""
    env["HOME"] = HOME_TEST_DIR
    home_dir = path.get_home_dir(True)
    # get_home_dir expands symlinks
    assert home_dir == os.path.realpath(env["HOME"])


@with_environment
def test_get_home_dir_4():
    """get_home_dir() still works if $HOME is not set"""

    if "HOME" in env:
        del env["HOME"]
    # this should still succeed, but we don't care what the answer is
    home = path.get_home_dir(False)


@skip_win32
@with_environment
def test_get_home_dir_5(monkeypatch):
    """raise HomeDirError if $HOME is specified, but not a writable dir"""
    env["HOME"] = abspath(HOME_TEST_DIR + "garbage")
    # set os.name = posix, to prevent My Documents fallback on Windows
    monkeypatch.setattr(os, "name", "posix")
    pytest.raises(path.HomeDirError, path.get_home_dir, True)


# Should we stub wreg fully so we can run the test on all platforms?
@skip_if_not_win32
@with_environment
def test_get_home_dir_8(monkeypatch):
    """Using registry hack for 'My Documents', os=='nt'

    HOMESHARE, HOMEDRIVE, HOMEPATH, USERPROFILE and others are missing.
    """
    monkeypatch.setattr(os, "name", "nt")
    # Remove from stub environment all keys that may be set
    for key in ["HOME", "HOMESHARE", "HOMEDRIVE", "HOMEPATH", "USERPROFILE"]:
        env.pop(key, None)

    class key:
        def __enter__(self):
            pass

        def Close(self):
            pass

        def __exit__(*args, **kwargs):
            pass

    with (
        patch.object(wreg, "OpenKey", return_value=key()),
        patch.object(wreg, "QueryValueEx", return_value=[abspath(HOME_TEST_DIR)]),
    ):
        home_dir = path.get_home_dir()
    assert home_dir == abspath(HOME_TEST_DIR)


@with_environment
def test_get_xdg_dir_0(monkeypatch):
    """test_get_xdg_dir_0, check xdg_dir"""
    monkeypatch.setattr(path, "_writable_dir", lambda path: True)
    monkeypatch.setattr(path, "get_home_dir", lambda: "somewhere")
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(sys, "platform", "linux2")
    env.pop("IPYTHON_DIR", None)
    env.pop("IPYTHONDIR", None)
    env.pop("XDG_CONFIG_HOME", None)

    assert path.get_xdg_dir() == os.path.join("somewhere", ".config")


@with_environment
def test_get_xdg_dir_1(monkeypatch):
    """test_get_xdg_dir_1, check nonexistent xdg_dir"""
    monkeypatch.setattr(path, "get_home_dir", lambda: HOME_TEST_DIR)
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(sys, "platform", "linux2")
    env.pop("IPYTHON_DIR", None)
    env.pop("IPYTHONDIR", None)
    env.pop("XDG_CONFIG_HOME", None)
    assert path.get_xdg_dir() is None


@with_environment
def test_get_xdg_dir_2(monkeypatch):
    """test_get_xdg_dir_2, check xdg_dir default to ~/.config"""
    monkeypatch.setattr(path, "get_home_dir", lambda: HOME_TEST_DIR)
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(sys, "platform", "linux2")
    env.pop("IPYTHON_DIR", None)
    env.pop("IPYTHONDIR", None)
    env.pop("XDG_CONFIG_HOME", None)
    cfgdir = os.path.join(path.get_home_dir(), ".config")
    if not os.path.exists(cfgdir):
        os.makedirs(cfgdir)

    assert path.get_xdg_dir() == cfgdir


@with_environment
def test_get_xdg_dir_3(monkeypatch):
    """test_get_xdg_dir_3, check xdg_dir not used on non-posix systems"""
    monkeypatch.setattr(path, "get_home_dir", lambda: HOME_TEST_DIR)
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(sys, "platform", "win32")
    env.pop("IPYTHON_DIR", None)
    env.pop("IPYTHONDIR", None)
    env.pop("XDG_CONFIG_HOME", None)
    cfgdir = os.path.join(path.get_home_dir(), ".config")
    os.makedirs(cfgdir, exist_ok=True)

    assert path.get_xdg_dir() is None


def test_filefind():
    """Various tests for filefind"""
    f = tempfile.NamedTemporaryFile()
    # print('fname:',f.name)
    alt_dirs = paths.get_ipython_dir()
    t = path.filefind(f.name, alt_dirs)
    # print('found:',t)


@dec.skip_if_not_win32
def test_get_long_path_name_win32():
    with TemporaryDirectory() as tmpdir:
        # Make a long path. Expands the path of tmpdir prematurely as it may already have a long
        # path component, so ensure we include the long form of it
        long_path = os.path.join(
            path.get_long_path_name(tmpdir), "this is my long path name"
        )
        os.makedirs(long_path)

        # Test to see if the short path evaluates correctly.
        short_path = os.path.join(tmpdir, "THISIS~1")
        evaluated_path = path.get_long_path_name(short_path)
        assert evaluated_path.lower() == long_path.lower()


@dec.skip_win32
def test_get_long_path_name():
    p = path.get_long_path_name("/usr/local")
    assert p == "/usr/local"


@dec.skip_win32  # can't create not-user-writable dir on win
@with_environment
def test_not_writable_ipdir():
    tmpdir = tempfile.mkdtemp()
    os.name = "posix"
    env.pop("IPYTHON_DIR", None)
    env.pop("IPYTHONDIR", None)
    env.pop("XDG_CONFIG_HOME", None)
    env["HOME"] = tmpdir
    ipdir = os.path.join(tmpdir, ".ipython")
    os.mkdir(ipdir, 0o555)
    try:
        open(os.path.join(ipdir, "_foo_"), "w", encoding="utf-8").close()
    except IOError:
        pass
    else:
        # I can still write to an unwritable dir,
        # assume I'm root and skip the test
        pytest.skip("I can't create directories that I can't write to")

    with pytest.warns(UserWarning, match="is not a writable location"):
        ipdir = paths.get_ipython_dir()
    env.pop("IPYTHON_DIR", None)


@with_environment
def test_get_py_filename():
    os.chdir(TMP_TEST_DIR)
    with make_tempfile("foo.py"):
        assert path.get_py_filename("foo.py") == "foo.py"
        assert path.get_py_filename("foo") == "foo.py"
    with make_tempfile("foo"):
        assert path.get_py_filename("foo") == "foo"
        pytest.raises(IOError, path.get_py_filename, "foo.py")
    pytest.raises(IOError, path.get_py_filename, "foo")
    pytest.raises(IOError, path.get_py_filename, "foo.py")
    true_fn = "foo with spaces.py"
    with make_tempfile(true_fn):
        assert path.get_py_filename("foo with spaces") == true_fn
        assert path.get_py_filename("foo with spaces.py") == true_fn
        pytest.raises(IOError, path.get_py_filename, '"foo with spaces.py"')
        pytest.raises(IOError, path.get_py_filename, "'foo with spaces.py'")


@onlyif_unicode_paths
def test_unicode_in_filename():
    """When a file doesn't exist, the exception raised should be safe to call
    str() on - i.e. in Python 2 it must only have ASCII characters.

    https://github.com/ipython/ipython/issues/875
    """
    try:
        # these calls should not throw unicode encode exceptions
        path.get_py_filename("fooéè.py")
    except IOError as ex:
        str(ex)


_GLOB_FILENAMES_A = ["a0", "a1", "a2"]
_GLOB_FILENAMES_B = ["0b", "1b", "2b"]
_GLOB_FILENAMES = _GLOB_FILENAMES_A + _GLOB_FILENAMES_B

_SHELLGLOB_COMMON = [
    (["*"], _GLOB_FILENAMES),
    (["a*"], _GLOB_FILENAMES_A),
    (["*c"], ["*c"]),
    (["*", "a*", "*b", "*c"], _GLOB_FILENAMES + _GLOB_FILENAMES_A + _GLOB_FILENAMES_B + ["*c"]),
    (["a[012]"], _GLOB_FILENAMES_A),
]

_SHELLGLOB_POSIX_EXTRA = [
    ([r"\*"], ["*"]),
    ([r"a\*", "a*"], ["a*"] + _GLOB_FILENAMES_A),
    ([r"a\[012]"], ["a[012]"]),
]

_SHELLGLOB_WINDOWS_EXTRA = [
    ([r"a\*", "a*"], [r"a\*"] + _GLOB_FILENAMES_A),
    ([r"a\[012]"], [r"a\[012]"]),
]


@pytest.fixture(scope="module")
def shellglob_tempdir(tmp_path_factory):
    td = tmp_path_factory.mktemp("shellglob")
    for fname in _GLOB_FILENAMES:
        (td / fname).write_text("", encoding="utf-8")
    return td


@skip_win32
@pytest.mark.parametrize("patterns,matches", _SHELLGLOB_COMMON + _SHELLGLOB_POSIX_EXTRA)
def test_shellglob_posix(shellglob_tempdir, monkeypatch, patterns, matches):
    monkeypatch.chdir(shellglob_tempdir)
    assert sorted(path.shellglob(patterns)) == sorted(matches)


@skip_if_not_win32
@pytest.mark.parametrize("patterns,matches", _SHELLGLOB_COMMON + _SHELLGLOB_WINDOWS_EXTRA)
def test_shellglob_windows(shellglob_tempdir, monkeypatch, patterns, matches):
    monkeypatch.chdir(shellglob_tempdir)
    assert sorted(path.shellglob(patterns)) == sorted(matches)


@pytest.mark.parametrize(
    "globstr, unescaped_globstr",
    [
        (r"\*\[\!\]\?", "*[!]?"),
        (r"\\*", r"\*"),
        (r"\\\*", r"\*"),
        (r"\\a", r"\a"),
        (r"\a", r"\a"),
    ],
)
def test_unescape_glob(globstr, unescaped_globstr):
    assert path.unescape_glob(globstr) == unescaped_globstr


@onlyif_unicode_paths
def test_ensure_dir_exists():
    with TemporaryDirectory() as td:
        d = os.path.join(td, "∂ir")
        path.ensure_dir_exists(d)  # create it
        assert os.path.isdir(d)
        path.ensure_dir_exists(d)  # no-op
        f = os.path.join(td, "ƒile")
        open(f, "w", encoding="utf-8").close()  # touch
        with pytest.raises(IOError):
            path.ensure_dir_exists(f)


@pytest.fixture
def link_or_copy_src(tmp_path):
    src = tmp_path / "src"
    src.write_text("Hello, world!", encoding="utf-8")
    return src


@skip_win32
def test_link_successful(link_or_copy_src, tmp_path):
    dst = str(tmp_path / "target")
    path.link_or_copy(str(link_or_copy_src), dst)
    assert os.stat(str(link_or_copy_src)).st_ino == os.stat(dst).st_ino


@skip_win32
def test_link_into_dir(link_or_copy_src, tmp_path):
    dst_dir = tmp_path / "some_dir"
    dst_dir.mkdir()
    path.link_or_copy(str(link_or_copy_src), str(dst_dir))
    expected_dst = dst_dir / link_or_copy_src.name
    assert os.stat(str(link_or_copy_src)).st_ino == os.stat(str(expected_dst)).st_ino


@skip_win32
def test_link_target_exists(link_or_copy_src, tmp_path):
    dst = tmp_path / "target"
    dst.write_text("", encoding="utf-8")
    path.link_or_copy(str(link_or_copy_src), str(dst))
    assert os.stat(str(link_or_copy_src)).st_ino == os.stat(str(dst)).st_ino


@skip_win32
def test_link_no_link(link_or_copy_src, tmp_path):
    real_link = os.link
    try:
        del os.link
        dst = str(tmp_path / "target")
        path.link_or_copy(str(link_or_copy_src), dst)
        with open(str(link_or_copy_src), "rb") as a_f, open(dst, "rb") as b_f:
            assert a_f.read() == b_f.read()
        assert os.stat(str(link_or_copy_src)).st_ino != os.stat(dst).st_ino
    finally:
        os.link = real_link


@skip_if_not_win32
def test_link_windows(link_or_copy_src, tmp_path):
    dst = str(tmp_path / "target")
    path.link_or_copy(str(link_or_copy_src), dst)
    with open(str(link_or_copy_src), "rb") as a_f, open(dst, "rb") as b_f:
        assert a_f.read() == b_f.read()


def test_link_twice(link_or_copy_src, tmp_path):
    # Linking the same file twice shouldn't leave duplicates around.
    # See https://github.com/ipython/ipython/issues/6450
    dst = str(tmp_path / "target")
    path.link_or_copy(str(link_or_copy_src), dst)
    path.link_or_copy(str(link_or_copy_src), dst)
    assert os.stat(str(link_or_copy_src)).st_ino == os.stat(dst).st_ino


@with_environment
def test_compress_user(tmp_path):
    """compress_user() only substitutes ~ on a path-component boundary."""
    home = str(tmp_path / "alice")
    env["HOME"] = home

    assert path.compress_user(join(home, "proj", "foo.py")) == join(
        "~", "proj", "foo.py"
    )
    assert path.compress_user(home) == "~"

    # A path that merely shares a prefix with home is not under it, so it must
    # come back untouched: "~-backup/lib" would expanduser to a different
    # (nonexistent) user's home rather than back to where it started.
    for sibling in (home + "-backup", home + "s"):
        p = join(sibling, "lib", "foo.py")
        assert path.compress_user(p) == p
        assert os.path.expanduser(path.compress_user(p)) == p
