# encoding: utf-8
"""Tests for IPython.utils.path.py"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import shutil
import sys
import tempfile

from os.path import join, abspath, split

import nose.tools as nt

from nose import with_setup

import IPython
from IPython.testing import decorators as dec
from IPython.testing.decorators import skip_if_not_win32, skip_win32
from IPython.utils import path

# Platform-dependent imports
try:
    import _winreg as wreg
except ImportError:
    #Fake _winreg module on none windows platforms
    import new
    sys.modules["_winreg"] = new.module("_winreg")
    import _winreg as wreg
    #Add entries that needs to be stubbed by the testing code
    (wreg.OpenKey, wreg.QueryValueEx,) = (None, None)

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
    oldstuff = (env.copy(), os.name, path.get_home_dir, IPython.__file__)

    if os.name == 'nt':
        platformstuff = (wreg.OpenKey, wreg.QueryValueEx,)


def teardown_environment():
    """Restore things that were remebered by the setup_environment function
    """
    (oldenv, os.name, path.get_home_dir, IPython.__file__,) = oldstuff
        
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
    
    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR).lower())


@with_environment
@skip_win32
def test_get_home_dir_3():
    """Testcase $HOME is set, then use its value as home directory."""
    env["HOME"] = HOME_TEST_DIR
    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, env["HOME"])


@with_environment
@skip_win32
def test_get_home_dir_4():
    """Testcase $HOME is not set, os=='posix'. 
    This should fail with HomeDirError"""
    
    os.name = 'posix'
    if 'HOME' in env: del env['HOME']
    nt.assert_raises(path.HomeDirError, path.get_home_dir)


@skip_if_not_win32
@with_environment
def test_get_home_dir_5():
    """Using HOMEDRIVE + HOMEPATH, os=='nt'.

    HOMESHARE is missing.
    """

    os.name = 'nt'
    env.pop('HOMESHARE', None)
    env['HOMEDRIVE'], env['HOMEPATH'] = os.path.splitdrive(HOME_TEST_DIR)
    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))


@skip_if_not_win32
@with_environment
def test_get_home_dir_6():
    """Using USERPROFILE, os=='nt'.

    HOMESHARE, HOMEDRIVE, HOMEPATH are missing.
    """

    os.name = 'nt'
    env.pop('HOMESHARE', None)
    env.pop('HOMEDRIVE', None)
    env.pop('HOMEPATH', None)
    env["USERPROFILE"] = abspath(HOME_TEST_DIR)
    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))


@skip_if_not_win32
@with_environment
def test_get_home_dir_7():
    """Using HOMESHARE, os=='nt'."""

    os.name = 'nt'
    env["HOMESHARE"] = abspath(HOME_TEST_DIR)
    home_dir = path.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))

    
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
    env['IPYTHON_DIR'] = env_ipdir
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, env_ipdir)


@with_environment
def test_get_ipython_dir_2():
    """test_get_ipython_dir_2, Testcase to see if we can call get_ipython_dir without Exceptions."""
    path.get_home_dir = lambda : "someplace"
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
    path.get_home_dir = lambda : 'somehome'
    path.get_xdg_dir = lambda : 'somexdg'
    os.name = "posix"
    env.pop('IPYTHON_DIR', None)
    env.pop('IPYTHONDIR', None)
    xdg_ipdir = os.path.join("somexdg", "ipython")
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, xdg_ipdir)

@with_environment
def test_get_ipython_dir_7():
    """test_get_ipython_dir_7, test home directory expansion on IPYTHON_DIR"""
    home_dir = os.path.expanduser('~')
    env['IPYTHON_DIR'] = os.path.join('~', 'somewhere')
    ipdir = path.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.join(home_dir, 'somewhere'))


@with_environment
def test_get_xdg_dir_1():
    """test_get_xdg_dir_1, check xdg_dir"""
    reload(path)
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

