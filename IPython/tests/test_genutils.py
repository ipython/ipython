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

import os, sys, IPython
env = os.environ

from os.path import join, abspath

try:
    import _winreg as wreg
except ImportError:
    pass

skip_if_not_win32 = skipif(sys.platform!='win32',"This test only runs under Windows")
    
def setup_environment():
    global oldstuff, platformstuff
    oldstuff = (env.copy(), os.name, genutils.get_home_dir, IPython.__file__,)

    if os.name=='nt':
        platformstuff=(wreg.OpenKey, wreg.QueryValueEx,)

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
    if os.name=='nt':
        (wreg.OpenKey, wreg.QueryValueEx,)=platformstuff

with_enivronment=with_setup(setup_environment, teardown_environment)

@with_enivronment
def test_get_home_dir_1():
    """Testcase to see if we can call get_home_dir without Exceptions."""
    home_dir = genutils.get_home_dir()
    
@with_enivronment
def test_get_home_dir_2():
    """Testcase for py2exe logic, un-compressed lib
    """
    sys.frozen=True
    
    #fake filename for IPython.__init__
    IPython.__file__=abspath(join(".", "home_test_dir/Lib/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))
    
@with_enivronment
def test_get_home_dir_3():
    """Testcase for py2exe logic, compressed lib
    """
    sys.frozen=True
    #fake filename for IPython.__init__
    IPython.__file__=abspath(join(".", "home_test_dir/Library.zip/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir")).lower()

@with_enivronment
def test_get_home_dir_4():
    """Testcase $HOME is set, then use its value as home directory."""
    env["HOME"]=join(".","home_test_dir")
    home_dir = genutils.get_home_dir()
    assert home_dir==env["HOME"]

@with_enivronment
def test_get_home_dir_5():
    """Testcase $HOME is not set, os=='posix'. 
    This should fail with HomeDirError"""
    
    os.name='posix'
    del os.environ["HOME"]
    try:
        genutils.get_home_dir()
        assert False
    except genutils.HomeDirError:
        pass
        
@with_enivronment
def test_get_home_dir_6():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] points to path."""
    
    os.name='nt'
    del os.environ["HOME"]
    env['HOMEDRIVE'],env['HOMEPATH']=os.path.abspath("."),"home_test_dir"

    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))

@with_enivronment
def test_get_home_dir_8():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] do not point to path.
    env['USERPROFILE'] points to path
    """

    os.name='nt'
    del os.environ["HOME"]
    env['HOMEDRIVE'],env['HOMEPATH']=os.path.abspath("."),"DOES NOT EXIST"
    env["USERPROFILE"]=abspath(join(".","home_test_dir"))

    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))



# Should we stub wreg fully so we can run the test on all platforms?
@skip_if_not_win32
@with_enivronment
def test_get_home_dir_9():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'], env['USERPROFILE'] missing
    """
    os.name='nt'
    del env["HOME"],env['HOMEDRIVE']

    #Stub windows registry functions
    def OpenKey(x,y):
        class key:
            def Close(self):
                pass
        return key()
    def QueryValueEx(x,y):
        return [abspath(join(".", "home_test_dir"))]

    wreg.OpenKey=OpenKey
    wreg.QueryValueEx=QueryValueEx

    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))


#
# Tests for get_ipython_dir
#

@with_enivronment
def test_get_ipython_dir_1():
    """1 Testcase to see if we can call get_ipython_dir without Exceptions."""
    ipdir = genutils.get_ipython_dir()


@with_enivronment
def test_get_ipython_dir_2():
    """2 Testcase to see if we can call get_ipython_dir without Exceptions."""
    env['IPYTHONDIR']="someplace/.ipython"
    ipdir = genutils.get_ipython_dir()
    assert ipdir == os.path.abspath("someplace/.ipython")


@with_enivronment
def test_get_ipython_dir_3():
    """3 Testcase to see if we can call get_ipython_dir without Exceptions."""
    genutils.get_home_dir=lambda : "someplace"
    os.name="posix"
    ipdir = genutils.get_ipython_dir()
    assert ipdir == os.path.abspath(os.path.join("someplace", ".ipython"))

@with_enivronment
def test_get_ipython_dir_4():
    """4 Testcase to see if we can call get_ipython_dir without Exceptions."""
    genutils.get_home_dir=lambda : "someplace"
    os.name="nt"
    ipdir = genutils.get_ipython_dir()
    assert ipdir == os.path.abspath(os.path.join("someplace", "_ipython"))



#
# Tests for get_security_dir
#

@with_enivronment
def test_get_security_dir():
    """Testcase to see if we can call get_security_dir without Exceptions."""
    sdir = genutils.get_security_dir()





def test_popkey_1():
    dct=dict(a=1, b=2, c=3)
    assert genutils.popkey(dct, "a")==1
    assert dct==dict(b=2, c=3)
    assert genutils.popkey(dct, "b")==2
    assert dct==dict(c=3)
    assert genutils.popkey(dct, "c")==3
    assert dct==dict()

@raises(KeyError)
def test_popkey_2():
    dct=dict(a=1, b=2, c=3)
    genutils.popkey(dct, "d")

def test_popkey_3():
    dct=dict(a=1, b=2, c=3)
    assert genutils.popkey(dct, "A", 13)==13
    assert dct==dict(a=1, b=2, c=3)
    assert genutils.popkey(dct, "B", 14)==14
    assert dct==dict(a=1, b=2, c=3)
    assert genutils.popkey(dct, "C", 15)==15
    assert dct==dict(a=1, b=2, c=3)
    assert genutils.popkey(dct, "a")==1
    assert dct==dict(b=2, c=3)
    assert genutils.popkey(dct, "b")==2
    assert dct==dict(c=3)
    assert genutils.popkey(dct, "c")==3
    assert dct==dict()
