from contextlib import contextmanager
import errno
import os
import shutil
import sys
import tempfile
import warnings

try:
    reload
except NameError:   # Python 3
    from imp import reload

from nose import with_setup
import nose.tools as nt

import IPython
from IPython import paths
from IPython.testing.decorators import skip_win32
from IPython.utils.tempdir import TemporaryDirectory

env = os.environ
TMP_TEST_DIR = tempfile.mkdtemp()
HOME_TEST_DIR = os.path.join(TMP_TEST_DIR, "home_test_dir")
XDG_TEST_DIR = os.path.join(HOME_TEST_DIR, "xdg_test_dir")
XDG_CACHE_DIR = os.path.join(HOME_TEST_DIR, "xdg_cache_dir")
IP_TEST_DIR = os.path.join(HOME_TEST_DIR,'.ipython')

def setup():
    """Setup testenvironment for the module:

            - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    os.makedirs(IP_TEST_DIR)
    os.makedirs(os.path.join(XDG_TEST_DIR, 'ipython'))
    os.makedirs(os.path.join(XDG_CACHE_DIR, 'ipython'))


def teardown():
    """Teardown testenvironment for the module:

            - Remove dummy home dir tree
    """
    # Note: we remove the parent test dir, which is the root of all test
    # subdirs we may have created.  Use shutil instead of os.removedirs, so
    # that non-empty directories are all recursively removed.
    shutil.rmtree(TMP_TEST_DIR)


def setup_environment():
    """Setup testenvironment for some functions that are tested
    in this module. In particular this functions stores attributes
    and other things that we need to stub in some test functions.
    This needs to be done on a function level and not module level because
    each testfunction needs a pristine environment.
    """
    global oldstuff, platformstuff
    oldstuff = (env.copy(), os.name, sys.platform, paths.get_home_dir, IPython.__file__, os.getcwd())

def teardown_environment():
    """Restore things that were remembered by the setup_environment function
    """
    (oldenv, os.name, sys.platform, paths.get_home_dir, IPython.__file__, old_wd) = oldstuff
    os.chdir(old_wd)
    reload(paths)

    for key in list(env):
        if key not in oldenv:
            del env[key]
    env.update(oldenv)
    if hasattr(sys, 'frozen'):
        del sys.frozen

# Build decorator that uses the setup_environment/setup_environment
with_environment = with_setup(setup_environment, teardown_environment)

@contextmanager
def patch_get_home_dir(dirpath):
    orig_get_home_dir = paths.get_home_dir
    paths.get_home_dir = lambda : dirpath
    try:
        yield
    finally:
        paths.get_home_dir = orig_get_home_dir


@with_environment
def test_get_ipython_dir_1():
    """test_get_ipython_dir_1, Testcase to see if we can call get_ipython_dir without Exceptions."""
    env_ipdir = os.path.join("someplace", ".ipython")
    paths._writable_dir = lambda path: True
    env['IPYTHONDIR'] = env_ipdir
    ipdir = paths.get_ipython_dir()
    nt.assert_equal(ipdir, env_ipdir)


@with_environment
def test_get_ipython_dir_2():
    """test_get_ipython_dir_2, Testcase to see if we can call get_ipython_dir without Exceptions."""
    with patch_get_home_dir('someplace'):
        paths.get_xdg_dir = lambda : None
        paths._writable_dir = lambda path: True
        os.name = "posix"
        env.pop('IPYTHON_DIR', None)
        env.pop('IPYTHONDIR', None)
        env.pop('XDG_CONFIG_HOME', None)
        ipdir = paths.get_ipython_dir()
        nt.assert_equal(ipdir, os.path.join("someplace", ".ipython"))

@with_environment
def test_get_ipython_dir_3():
    """test_get_ipython_dir_3, move XDG if defined, and .ipython doesn't exist."""
    tmphome = TemporaryDirectory()
    try:
        with patch_get_home_dir(tmphome.name):
            os.name = "posix"
            env.pop('IPYTHON_DIR', None)
            env.pop('IPYTHONDIR', None)
            env['XDG_CONFIG_HOME'] = XDG_TEST_DIR

            with warnings.catch_warnings(record=True) as w:
                ipdir = paths.get_ipython_dir()

            nt.assert_equal(ipdir, os.path.join(tmphome.name, ".ipython"))
            if sys.platform != 'darwin':
                nt.assert_equal(len(w), 1)
                nt.assert_in('Moving', str(w[0]))
    finally:
        tmphome.cleanup()

@with_environment
def test_get_ipython_dir_4():
    """test_get_ipython_dir_4, warn if XDG and home both exist."""
    with patch_get_home_dir(HOME_TEST_DIR):
        os.name = "posix"
        env.pop('IPYTHON_DIR', None)
        env.pop('IPYTHONDIR', None)
        env['XDG_CONFIG_HOME'] = XDG_TEST_DIR
        try:
            os.mkdir(os.path.join(XDG_TEST_DIR, 'ipython'))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with warnings.catch_warnings(record=True) as w:
            ipdir = paths.get_ipython_dir()

        nt.assert_equal(ipdir, os.path.join(HOME_TEST_DIR, ".ipython"))
        if sys.platform != 'darwin':
            nt.assert_equal(len(w), 1)
            nt.assert_in('Ignoring', str(w[0]))

@with_environment
def test_get_ipython_dir_5():
    """test_get_ipython_dir_5, use .ipython if exists and XDG defined, but doesn't exist."""
    with patch_get_home_dir(HOME_TEST_DIR):
        os.name = "posix"
        env.pop('IPYTHON_DIR', None)
        env.pop('IPYTHONDIR', None)
        env['XDG_CONFIG_HOME'] = XDG_TEST_DIR
        try:
            os.rmdir(os.path.join(XDG_TEST_DIR, 'ipython'))
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        ipdir = paths.get_ipython_dir()
        nt.assert_equal(ipdir, IP_TEST_DIR)

@with_environment
def test_get_ipython_dir_6():
    """test_get_ipython_dir_6, use home over XDG if defined and neither exist."""
    xdg = os.path.join(HOME_TEST_DIR, 'somexdg')
    os.mkdir(xdg)
    shutil.rmtree(os.path.join(HOME_TEST_DIR, '.ipython'))
    with patch_get_home_dir(HOME_TEST_DIR):
        orig_get_xdg_dir = paths.get_xdg_dir
        paths.get_xdg_dir = lambda : xdg
        try:
            os.name = "posix"
            env.pop('IPYTHON_DIR', None)
            env.pop('IPYTHONDIR', None)
            env.pop('XDG_CONFIG_HOME', None)
            with warnings.catch_warnings(record=True) as w:
                ipdir = paths.get_ipython_dir()

            nt.assert_equal(ipdir, os.path.join(HOME_TEST_DIR, '.ipython'))
            nt.assert_equal(len(w), 0)
        finally:
            paths.get_xdg_dir = orig_get_xdg_dir

@with_environment
def test_get_ipython_dir_7():
    """test_get_ipython_dir_7, test home directory expansion on IPYTHONDIR"""
    paths._writable_dir = lambda path: True
    home_dir = os.path.normpath(os.path.expanduser('~'))
    env['IPYTHONDIR'] = os.path.join('~', 'somewhere')
    ipdir = paths.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.join(home_dir, 'somewhere'))

@skip_win32
@with_environment
def test_get_ipython_dir_8():
    """test_get_ipython_dir_8, test / home directory"""
    old = paths._writable_dir, paths.get_xdg_dir
    try:
        paths._writable_dir = lambda path: bool(path)
        paths.get_xdg_dir = lambda: None
        env.pop('IPYTHON_DIR', None)
        env.pop('IPYTHONDIR', None)
        env['HOME'] = '/'
        nt.assert_equal(paths.get_ipython_dir(), '/.ipython')
    finally:
        paths._writable_dir, paths.get_xdg_dir = old


@with_environment
def test_get_ipython_cache_dir():
    os.environ["HOME"] = HOME_TEST_DIR
    if os.name == 'posix' and sys.platform != 'darwin':
        # test default
        os.makedirs(os.path.join(HOME_TEST_DIR, ".cache"))
        os.environ.pop("XDG_CACHE_HOME", None)
        ipdir = paths.get_ipython_cache_dir()
        nt.assert_equal(os.path.join(HOME_TEST_DIR, ".cache", "ipython"),
                        ipdir)
        nt.assert_true(os.path.isdir(ipdir))

        # test env override
        os.environ["XDG_CACHE_HOME"] = XDG_CACHE_DIR
        ipdir = paths.get_ipython_cache_dir()
        nt.assert_true(os.path.isdir(ipdir))
        nt.assert_equal(ipdir, os.path.join(XDG_CACHE_DIR, "ipython"))
    else:
        nt.assert_equal(paths.get_ipython_cache_dir(),
                        paths.get_ipython_dir())

def test_get_ipython_package_dir():
    ipdir = paths.get_ipython_package_dir()
    nt.assert_true(os.path.isdir(ipdir))


def test_get_ipython_module_path():
    ipapp_path = paths.get_ipython_module_path('IPython.terminal.ipapp')
    nt.assert_true(os.path.isfile(ipapp_path))
