# encoding: utf-8

"""Tests for genutils.py"""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib
import os
import shutil
import sys
import tempfile

from os.path import join, abspath, split

# third-party
import nose.tools as nt

from nose import with_setup
from nose.tools import raises

# Our own
import IPython
from IPython import genutils
from IPython.testing.decorators import skipif, skip_if_not_win32

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
IP_TEST_DIR = join(HOME_TEST_DIR,'_ipython')
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
    oldstuff = (env.copy(), os.name, genutils.get_home_dir, IPython.__file__,)

    if os.name == 'nt':
        platformstuff = (wreg.OpenKey, wreg.QueryValueEx,)

    if 'IPYTHONDIR' in env:
        del env['IPYTHONDIR']

def teardown_environment():
    """Restore things that were remebered by the setup_environment function
    """
    (oldenv, os.name, genutils.get_home_dir, IPython.__file__,) = oldstuff
    for key in env.keys():
        if key not in oldenv:
            del env[key]
    env.update(oldenv)
    if hasattr(sys, 'frozen'):
        del sys.frozen
    if os.name == 'nt':
        (wreg.OpenKey, wreg.QueryValueEx,) = platformstuff

# Build decorator that uses the setup_environment/setup_environment
with_enivronment = with_setup(setup_environment, teardown_environment)


#
# Tests for get_home_dir
#

@skip_if_not_win32
@with_enivronment
def test_get_home_dir_1():
    """Testcase for py2exe logic, un-compressed lib
    """
    sys.frozen = True
    
    #fake filename for IPython.__init__
    IPython.__file__ = abspath(join(HOME_TEST_DIR, "Lib/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))
    
@skip_if_not_win32
@with_enivronment
def test_get_home_dir_2():
    """Testcase for py2exe logic, compressed lib
    """
    sys.frozen = True
    #fake filename for IPython.__init__
    IPython.__file__ = abspath(join(HOME_TEST_DIR, "Library.zip/IPython/__init__.py")).lower()
    
    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR).lower())

@with_enivronment
def test_get_home_dir_3():
    """Testcase $HOME is set, then use its value as home directory."""
    env["HOME"] = HOME_TEST_DIR
    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, env["HOME"])

@with_enivronment
def test_get_home_dir_4():
    """Testcase $HOME is not set, os=='poix'. 
    This should fail with HomeDirError"""
    
    os.name = 'posix'
    if 'HOME' in env: del env['HOME']
    nt.assert_raises(genutils.HomeDirError, genutils.get_home_dir)
        
@skip_if_not_win32
@with_enivronment
def test_get_home_dir_5():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] points to path."""

    os.name = 'nt'
    if 'HOME' in env: del env['HOME']
    env['HOMEDRIVE'], env['HOMEPATH'] = os.path.splitdrive(HOME_TEST_DIR)

    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))

@skip_if_not_win32
@with_enivronment
def test_get_home_dir_6():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] do not point to path.
    env['USERPROFILE'] points to path
    """

    os.name = 'nt'
    if 'HOME' in env: del env['HOME']
    env['HOMEDRIVE'], env['HOMEPATH'] = os.path.abspath(TEST_FILE_PATH), "DOES NOT EXIST"
    env["USERPROFILE"] = abspath(HOME_TEST_DIR)

    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))

# Should we stub wreg fully so we can run the test on all platforms?
@skip_if_not_win32
@with_enivronment
def test_get_home_dir_7():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'], env['USERPROFILE'] missing
    """
    os.name = 'nt'
    if 'HOME' in env: del env['HOME']
    if 'HOMEDRIVE' in env: del env['HOMEDRIVE']

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

    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(HOME_TEST_DIR))

#
# Tests for get_ipython_dir
#

@with_enivronment
def test_get_ipython_dir_1():
    """test_get_ipython_dir_1, Testcase to see if we can call get_ipython_dir without Exceptions."""
    env['IPYTHONDIR'] = "someplace/.ipython"
    ipdir = genutils.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.abspath("someplace/.ipython"))


@with_enivronment
def test_get_ipython_dir_2():
    """test_get_ipython_dir_2, Testcase to see if we can call get_ipython_dir without Exceptions."""
    genutils.get_home_dir = lambda : "someplace"
    os.name = "posix"
    ipdir = genutils.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.abspath(os.path.join("someplace", ".ipython")))

@with_enivronment
def test_get_ipython_dir_3():
    """test_get_ipython_dir_3, Testcase to see if we can call get_ipython_dir without Exceptions."""
    genutils.get_home_dir = lambda : "someplace"
    os.name = "nt"
    ipdir = genutils.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.abspath(os.path.join("someplace", "_ipython")))

#
# Tests for get_security_dir
#

@with_enivronment
def test_get_security_dir():
    """Testcase to see if we can call get_security_dir without Exceptions."""
    sdir = genutils.get_security_dir()

#
# Tests for get_log_dir
#

@with_enivronment
def test_get_log_dir():
    """Testcase to see if we can call get_log_dir without Exceptions."""
    sdir = genutils.get_log_dir()

#
# Tests for popkey
#

def test_popkey_1():
    """test_popkey_1, Basic usage test of popkey
    """
    dct = dict(a=1, b=2, c=3)
    nt.assert_equal(genutils.popkey(dct, "a"), 1)
    nt.assert_equal(dct, dict(b=2, c=3))
    nt.assert_equal(genutils.popkey(dct, "b"), 2)
    nt.assert_equal(dct, dict(c=3))
    nt.assert_equal(genutils.popkey(dct, "c"), 3)
    nt.assert_equal(dct, dict())

def test_popkey_2():
    """test_popkey_2, Test to see that popkey of non occuring keys
    generates a KeyError exception
    """
    dct = dict(a=1, b=2, c=3)
    nt.assert_raises(KeyError, genutils.popkey, dct, "d")

def test_popkey_3():
    """test_popkey_3, Tests to see that popkey calls returns the correct value
    and that the key/value was removed from the dict.
    """
    dct = dict(a=1, b=2, c=3)
    nt.assert_equal(genutils.popkey(dct, "A", 13), 13)
    nt.assert_equal(dct, dict(a=1, b=2, c=3))
    nt.assert_equal(genutils.popkey(dct, "B", 14), 14)
    nt.assert_equal(dct, dict(a=1, b=2, c=3))
    nt.assert_equal(genutils.popkey(dct, "C", 15), 15)
    nt.assert_equal(dct, dict(a=1, b=2, c=3))
    nt.assert_equal(genutils.popkey(dct, "a"), 1)
    nt.assert_equal(dct, dict(b=2, c=3))
    nt.assert_equal(genutils.popkey(dct, "b"), 2)
    nt.assert_equal(dct, dict(c=3))
    nt.assert_equal(genutils.popkey(dct, "c"), 3)
    nt.assert_equal(dct, dict())
