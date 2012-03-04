# encoding: utf-8
"""Tests for IPython.utils.path.py"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import os
import shutil
import sys
import tempfile
from io import StringIO

from os.path import join, abspath, split

import nose.tools as nt

from nose import with_setup

import IPython
from IPython.testing import decorators as dec
from IPython.testing.decorators import skip_if_not_win32, skip_win32
from IPython.testing.tools import make_tempfile, AssertPrints
from IPython.utils import path, io
from IPython.utils import py3compat

# Platform-dependent imports
try:
    import _winreg as wreg
except ImportError:
    #Fake _winreg module on none windows platforms
    import types
    wr_name = "winreg" if py3compat.PY3 else "_winreg"
    sys.modules[wr_name] = types.ModuleType(wr_name)
    import _winreg as wreg
    #Add entries that needs to be stubbed by the testing code
    (wreg.OpenKey, wreg.QueryValueEx,) = (None, None)

try:
    reload
except NameError:   # Python 3
    from imp import reload

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
env = os.environ
TEST_FILE_PATH = split(abspath(__file__))[0]
TMP_TEST_DIR = tempfile.mkdtemp()
HOME_TEST_DIR = join(TMP_TEST_DIR, "home_test_dir")
XDG_TEST_DIR = join(HOME_TEST_DIR, "xdg_test_dir")
IP_TEST_DIR = join(HOME_TEST_DIR,'.ipython')
#
# Setup/teardown functions/decorators
#

def setup():
    """Setup testenvironment for the module:

            - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    os.makedirs(IP_TEST_DIR)
    os.makedirs(os.path.join(XDG_TEST_DIR, 'ipython'))


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
    oldstuff = (env.copy(), os.name, path.get_home_dir, IPython.__file__, os.getcwd())

    if os.name == 'nt':
        platformstuff = (wreg.OpenKey, wreg.QueryValueEx,)


def teardown_environment():
    """Restore things that were remebered by the setup_environment function
    """
    (oldenv, os.name, path.get_home_dir, IPython.__file__, old_wd) = oldstuff
    os.chdir(old_wd)
    reload(path)

    for key in env.keys():
        if key not in oldenv:
            del env[key]
    env.update(oldenv)
    if hasattr(sys, 'frozen'):
        del sys.frozen
    if os.name == 'nt':
        (wreg.OpenKey, wreg.QueryValueEx,) = platformstuff

# Build decorator that uses the setup_environment/setup_environment
with_environment = with_setup(setup_environment, teardown_environment)

@skip_if_not_win32
@with_environment
def test_get_home_dir_1():
    """Testcase for py2exe logic, un-compressed lib
    """
    sys.frozen = True

    #fake filename for IPython.__init__
    IPython.__file__ = abspath(join(HOME_TEST_DIR, "Lib/IPython/__init__.py"))

    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))


@skip_if_not_win32
@with_environment
def test_get_home_dir_2():
    """Testcase for py2exe logic, compressed lib
    """
    sys.frozen = True
    #fake filename for IPython.__init__
    IPython.__file__ = abspath(join(HOME_TEST_DIR, "Library.zip/IPython/__init__.py")).lower()

    home_dir = path.get_home_dir(True)
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR).lower())


@with_environment
def test_get_home_dir_3():
    """get_home_dir() uses $HOME if set"""
    env["HOME"] = HOME_TEST_DIR
    home_dir = path.get_home_dir(True)
    # get_home_dir expands symlinks
    nt.assert_equal(home_dir, os.path.realpath(env["HOME"]))


@with_environment
def test_get_home_dir_4():
    """get_home_dir() still works if $HOME is not set"""

    if 'HOME' in env: del env['HOME']
    # this should still succeed, but we don't know what the answer should be
    home = path.get_home_dir(True)
    nt.assert_true(path._writable_dir(home))

@with_environment
def test_get_home_dir_5():
    """raise HomeDirError if $HOME is specified, but not a writable dir"""
    env['HOME'] = abspath(HOME_TEST_DIR+'garbage')
    # set os.name = posix, to prevent My Documents fallback on Windows
    os.name = 'posix'
    nt.assert_raises(path.HomeDirError, path.get_home_dir, True)


# Should we stub wreg fully so we can run the test on all platforms?
@skip_if_not_win32
@with_environment
def test_get_home_dir_8():
    """Using registry hack for 'My Documents', os=='nt'

    HOMESHARE, HOMEDRIVE, HOMEPATH, USERPROFILE and others are missing.
    """
    os.name = 'nt'
    # Remove from stub environment all keys that may be set
    for key in ['HOME', 'HOMESHARE', 'HOMEDRIVE', 'HOMEPATH', 'USERPROFILE']:
        env.pop(key, None)

    #Stub windows registry functions
    def OpenKey(x, y):
        class key:
            def Close(self):
                pass
        return key()
    def QueryValueEx(x, y):
        return [abspath(HOME_TEST_DIR)]

    wreg.OpenKey = OpenKey
    wreg.QueryValueEx = QueryValueEx

    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))


@with_environment
def test_get_ipython_dir_1():
    """test_get_ipython_dir_1, Testcase to see if we can call get_ipython_dir without Exceptions."""
    env_ipdir = os.path.join("someplace", ".ipython")
    path._writable_dir = lambda path: True
    env['IPYTHON_DIR'] = env_ipdir
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, env_ipdir)


@with_environment
def test_get_ipython_dir_2():
    """test_get_ipython_dir_2, Testcase to see if we can call get_ipython_dir without Exceptions."""
    path.get_home_dir = lambda : "someplace"
    path.get_xdg_dir = lambda : None
    path._writable_dir = lambda path: True
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env.pop('XDG_CONFIG_HOME', None)
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.join("someplace", ".ipython"))

@with_environment
def test_get_ipython_dir_3():
    """test_get_ipython_dir_3, use XDG if defined, and .ipython doesn't exist."""
    path.get_home_dir = lambda : "someplace"
    path._writable_dir = lambda path: True
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env['XDG_CONFIG_HOME'] = XDG_TEST_DIR
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.join(XDG_TEST_DIR, "ipython"))

@with_environment
def test_get_ipython_dir_4():
    """test_get_ipython_dir_4, use XDG if both exist."""
    path.get_home_dir = lambda : HOME_TEST_DIR
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env['XDG_CONFIG_HOME'] = XDG_TEST_DIR
    xdg_ipdir = os.path.join(XDG_TEST_DIR, "ipython")
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, xdg_ipdir)

@with_environment
def test_get_ipython_dir_5():
    """test_get_ipython_dir_5, use .ipython if exists and XDG defined, but doesn't exist."""
    path.get_home_dir = lambda : HOME_TEST_DIR
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env['XDG_CONFIG_HOME'] = XDG_TEST_DIR
    os.rmdir(os.path.join(XDG_TEST_DIR, 'ipython'))
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, IP_TEST_DIR)

@with_environment
def test_get_ipython_dir_6():
    """test_get_ipython_dir_6, use XDG if defined and neither exist."""
    xdg = os.path.join(HOME_TEST_DIR, 'somexdg')
    os.mkdir(xdg)
    shutil.rmtree(os.path.join(HOME_TEST_DIR, '.ipython'))
    path.get_home_dir = lambda : HOME_TEST_DIR
    path.get_xdg_dir = lambda : xdg
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env.pop('XDG_CONFIG_HOME', None)
    xdg_ipdir = os.path.join(xdg, "ipython")
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, xdg_ipdir)

@with_environment
def test_get_ipython_dir_7():
    """test_get_ipython_dir_7, test home directory expansion on IPYTHON_DIR"""
    path._writable_dir = lambda path: True
    home_dir = os.path.expanduser('~')
    env['IPYTHON_DIR'] = os.path.join('~', 'somewhere')
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.join(home_dir, 'somewhere'))


@with_environment
def test_get_xdg_dir_1():
    """test_get_xdg_dir_1, check xdg_dir"""
    reload(path)
    path._writable_dir = lambda path: True
    path.get_home_dir = lambda : 'somewhere'
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env.pop('XDG_CONFIG_HOME', None)

    nt.assert_equal(path.get_xdg_dir(), os.path.join('somewhere', '.config'))


@with_environment
def test_get_xdg_dir_1():
    """test_get_xdg_dir_1, check nonexistant xdg_dir"""
    reload(path)
    path.get_home_dir = lambda : HOME_TEST_DIR
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env.pop('XDG_CONFIG_HOME', None)
    nt.assert_equal(path.get_xdg_dir(), None)

@with_environment
def test_get_xdg_dir_2():
    """test_get_xdg_dir_2, check xdg_dir default to ~/.config"""
    reload(path)
    path.get_home_dir = lambda : HOME_TEST_DIR
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env.pop('XDG_CONFIG_HOME', None)
    cfgdir=os.path.join(path.get_home_dir(), '.config')
    os.makedirs(cfgdir)

    nt.assert_equal(path.get_xdg_dir(), cfgdir)

def test_filefind():
    """Various tests for filefind"""
    f = tempfile.NamedTemporaryFile()
    # print 'fname:',f.name
    alt_dirs = path.get_ipython_dir()
    t = path.filefind(f.name, alt_dirs)
    # print 'found:',t


def test_get_ipython_package_dir():
    ipdir = path.get_ipython_package_dir()
    nt.assert_true(os.path.isdir(ipdir))


def test_get_ipython_module_path():
    ipapp_path = path.get_ipython_module_path('IPython.frontend.terminal.ipapp')
    nt.assert_true(os.path.isfile(ipapp_path))


@dec.skip_if_not_win32
def test_get_long_path_name_win32():
    p = path.get_long_path_name('c:\\docume~1')
    nt.assert_equals(p,u'c:\\Documents and Settings')


@dec.skip_win32
def test_get_long_path_name():
    p = path.get_long_path_name('/usr/local')
    nt.assert_equals(p,'/usr/local')

@dec.skip_win32 # can't create not-user-writable dir on win
@with_environment
def test_not_writable_ipdir():
    tmpdir = tempfile.mkdtemp()
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    env.pop('XDG_CONFIG_HOME', None)
    env['HOME'] = tmpdir
    ipdir = os.path.join(tmpdir, '.ipython')
    os.mkdir(ipdir)
    os.chmod(ipdir, 600)
    with AssertPrints('is not a writable location', channel='stderr'):
        ipdir = path.get_ipython_dir()
    env.pop('IPYTHON_DIR', None)

def test_unquote_filename():
    for win32 in (True, False):
        nt.assert_equals(path.unquote_filename('foo.py', win32=win32), 'foo.py')
        nt.assert_equals(path.unquote_filename('foo bar.py', win32=win32), 'foo bar.py')
    nt.assert_equals(path.unquote_filename('"foo.py"', win32=True), 'foo.py')
    nt.assert_equals(path.unquote_filename('"foo bar.py"', win32=True), 'foo bar.py')
    nt.assert_equals(path.unquote_filename("'foo.py'", win32=True), 'foo.py')
    nt.assert_equals(path.unquote_filename("'foo bar.py'", win32=True), 'foo bar.py')
    nt.assert_equals(path.unquote_filename('"foo.py"', win32=False), '"foo.py"')
    nt.assert_equals(path.unquote_filename('"foo bar.py"', win32=False), '"foo bar.py"')
    nt.assert_equals(path.unquote_filename("'foo.py'", win32=False), "'foo.py'")
    nt.assert_equals(path.unquote_filename("'foo bar.py'", win32=False), "'foo bar.py'")

@with_environment
def test_get_py_filename():
    os.chdir(TMP_TEST_DIR)
    for win32 in (True, False):
        with make_tempfile('foo.py'):
            nt.assert_equals(path.get_py_filename('foo.py', force_win32=win32), 'foo.py')
            nt.assert_equals(path.get_py_filename('foo', force_win32=win32), 'foo.py')
        with make_tempfile('foo'):
            nt.assert_equals(path.get_py_filename('foo', force_win32=win32), 'foo')
            nt.assert_raises(IOError, path.get_py_filename, 'foo.py', force_win32=win32)
        nt.assert_raises(IOError, path.get_py_filename, 'foo', force_win32=win32)
        nt.assert_raises(IOError, path.get_py_filename, 'foo.py', force_win32=win32)
        true_fn = 'foo with spaces.py'
        with make_tempfile(true_fn):
            nt.assert_equals(path.get_py_filename('foo with spaces', force_win32=win32), true_fn)
            nt.assert_equals(path.get_py_filename('foo with spaces.py', force_win32=win32), true_fn)
            if win32:
                nt.assert_equals(path.get_py_filename('"foo with spaces.py"', force_win32=True), true_fn)
                nt.assert_equals(path.get_py_filename("'foo with spaces.py'", force_win32=True), true_fn)
            else:
                nt.assert_raises(IOError, path.get_py_filename, '"foo with spaces.py"', force_win32=False)
                nt.assert_raises(IOError, path.get_py_filename, "'foo with spaces.py'", force_win32=False)
                
def test_unicode_in_filename():
    """When a file doesn't exist, the exception raised should be safe to call
    str() on - i.e. in Python 2 it must only have ASCII characters.
    
    https://github.com/ipython/ipython/issues/875
    """
    try:
        # these calls should not throw unicode encode exceptions
        path.get_py_filename(u'fooéè.py',  force_win32=False)
    except IOError as ex:
        str(ex)
