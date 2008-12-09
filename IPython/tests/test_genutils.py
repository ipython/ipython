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

from IPython import genutils
from IPython.testing.decorators import skipif
from nose import with_setup
from nose.tools import raises

from os.path import join, abspath, split
import os, sys, IPython
import nose.tools as nt

env = os.environ

try:
    import _winreg as wreg
except ImportError:
    #Fake _winreg module on none windows platforms
    import new
    sys.modules["_winreg"] = new.module("_winreg")
    import _winreg as wreg
    #Add entries that needs to be stubbed by the testing code
    (wreg.OpenKey, wreg.QueryValueEx,) = (None, None)

test_file_path = split(abspath(__file__))[0]

#

def setup():
    try:
        os.makedirs("home_test_dir/_ipython")
    except WindowsError:
        pass #Or should we complain that the test directory already exists??

def teardown():
    try:
        os.removedirs("home_test_dir/_ipython")
    except WindowsError:
        pass #Or should we complain that the test directory already exists??

    
def setup_environment():
    global oldstuff, platformstuff
    oldstuff = (env.copy(), os.name, genutils.get_home_dir, IPython.__file__,)

    if os.name == 'nt':
        platformstuff = (wreg.OpenKey, wreg.QueryValueEx,)

    if 'IPYTHONDIR' in env:
        del env['IPYTHONDIR']

def teardown_environment():
    (oldenv, os.name, genutils.get_home_dir, IPython.__file__,) = oldstuff
    for key in env.keys():
        if key not in oldenv:
            del env[key]
    env.update(oldenv)
    if hasattr(sys, 'frozen'):
        del sys.frozen
    if os.name == 'nt':
        (wreg.OpenKey, wreg.QueryValueEx,) = platformstuff

with_enivronment = with_setup(setup_environment, teardown_environment)

@with_enivronment
def test_get_home_dir_1():
    """Testcase for py2exe logic, un-compressed lib
    """
    sys.frozen = True
    
    #fake filename for IPython.__init__
    IPython.__file__ = abspath(join(test_file_path, "home_test_dir/Lib/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(join(test_file_path, "home_test_dir")))
    
@with_enivronment
def test_get_home_dir_2():
    """Testcase for py2exe logic, compressed lib
    """
    sys.frozen = True
    #fake filename for IPython.__init__
    IPython.__file__ = abspath(join(test_file_path, "home_test_dir/Library.zip/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(join(test_file_path, "home_test_dir")).lower())

@with_enivronment
def test_get_home_dir_3():
    """Testcase $HOME is set, then use its value as home directory."""
    env["HOME"] = join(test_file_path, "home_test_dir")
    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, env["HOME"])

@with_enivronment
def test_get_home_dir_4():
    """Testcase $HOME is not set, os=='posix'. 
    This should fail with HomeDirError"""
    
    os.name = 'posix'
    del os.environ["HOME"]
    nt.assert_raises(genutils.HomeDirError, genutils.get_home_dir)
        
@with_enivronment
def test_get_home_dir_5():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] points to path."""
    
    os.name = 'nt'
    del os.environ["HOME"]
    env['HOMEDRIVE'], env['HOMEPATH'] = os.path.abspath(test_file_path), "home_test_dir"

    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(join(test_file_path, "home_test_dir")))

@with_enivronment
def test_get_home_dir_6():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] do not point to path.
    env['USERPROFILE'] points to path
    """

    os.name = 'nt'
    del os.environ["HOME"]
    env['HOMEDRIVE'], env['HOMEPATH'] = os.path.abspath(test_file_path), "DOES NOT EXIST"
    env["USERPROFILE"] = abspath(join(test_file_path, "home_test_dir"))

    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(join(test_file_path, "home_test_dir")))

# Should we stub wreg fully so we can run the test on all platforms?
#@skip_if_not_win32
@with_enivronment
def test_get_home_dir_7():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'], env['USERPROFILE'] missing
    """
    os.name = 'nt'
    del env["HOME"], env['HOMEDRIVE']

    #Stub windows registry functions
    def OpenKey(x, y):
        class key:
            def Close(self):
                pass
        return key()
    def QueryValueEx(x, y):
        return [abspath(join(test_file_path, "home_test_dir"))]

    wreg.OpenKey = OpenKey
    wreg.QueryValueEx = QueryValueEx

    home_dir = genutils.get_home_dir()
    nt.assert_equal(home_dir, abspath(join(test_file_path, "home_test_dir")))


#
# Tests for get_ipython_dir
#

@with_enivronment
def test_get_ipython_dir_1():
    """2 Testcase to see if we can call get_ipython_dir without Exceptions."""
    env['IPYTHONDIR'] = "someplace/.ipython"
    ipdir = genutils.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.abspath("someplace/.ipython"))


@with_enivronment
def test_get_ipython_dir_2():
    """3 Testcase to see if we can call get_ipython_dir without Exceptions."""
    genutils.get_home_dir = lambda : "someplace"
    os.name = "posix"
    ipdir = genutils.get_ipython_dir()
    nt.assert_equal(ipdir, os.path.abspath(os.path.join("someplace", ".ipython")))

@with_enivronment
def test_get_ipython_dir_3():
    """4 Testcase to see if we can call get_ipython_dir without Exceptions."""
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
# Tests for popkey
#

def test_popkey_1():
    dct = dict(a=1, b=2, c=3)
    nt.assert_equal(genutils.popkey(dct, "a"), 1)
    nt.assert_equal(dct, dict(b=2, c=3))
    nt.assert_equal(genutils.popkey(dct, "b"), 2)
    nt.assert_equal(dct, dict(c=3))
    nt.assert_equal(genutils.popkey(dct, "c"), 3)
    nt.assert_equal(dct, dict())

def test_popkey_2():
    dct = dict(a=1, b=2, c=3)
    nt.assert_raises(KeyError, genutils.popkey, dct, "d")

def test_popkey_3():
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
