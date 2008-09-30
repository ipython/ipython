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

import os, sys, IPython
env = os.environ

from os.path import join, abspath

def test_get_home_dir_1():
    """Testcase to see if we can call get_home_dir without Exceptions."""
    home_dir = genutils.get_home_dir()
    
def test_get_home_dir_2():
    """Testcase for py2exe logic, un-compressed lib
    """
    sys.frozen=True
    oldstuff=IPython.__file__
    
    #fake filename for IPython.__init__
    IPython.__file__=abspath(join(".", "home_test_dir/Lib/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))
    IPython.__file__=oldstuff
    del sys.frozen
    
def test_get_home_dir_3():
    """Testcase for py2exe logic, compressed lib
    """
    
    sys.frozen=True
    oldstuff=IPython.__file__
    
    #fake filename for IPython.__init__
    IPython.__file__=abspath(join(".", "home_test_dir/Library.zip/IPython/__init__.py"))
    
    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir")).lower()

    del sys.frozen
    IPython.__file__=oldstuff


def test_get_home_dir_4():
    """Testcase $HOME is set, then use its value as home directory."""
    oldstuff=env["HOME"]

    env["HOME"]=join(".","home_test_dir")
    home_dir = genutils.get_home_dir()
    assert home_dir==env["HOME"]
    
    env["HOME"]=oldstuff

def test_get_home_dir_5():
    """Testcase $HOME is not set, os=='posix'. 
    This should fail with HomeDirError"""
    oldstuff=env["HOME"],os.name
    
    os.name='posix'
    del os.environ["HOME"]
    try:
        genutils.get_home_dir()
        assert False
    except genutils.HomeDirError:
        pass
    finally:
        env["HOME"],os.name=oldstuff
        
def test_get_home_dir_6():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] points to path."""
    
    oldstuff=env["HOME"],os.name,env['HOMEDRIVE'],env['HOMEPATH']
    
    os.name='nt'
    del os.environ["HOME"]
    env['HOMEDRIVE'],env['HOMEPATH']=os.path.abspath("."),"home_test_dir"

    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))
    
    env["HOME"],os.name,env['HOMEDRIVE'],env['HOMEPATH']=oldstuff

def test_get_home_dir_8():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'] do not point to path.
    env['USERPROFILE'] points to path
    """
    oldstuff=(env["HOME"],os.name,env['HOMEDRIVE'],env['HOMEPATH'])
    
    os.name='nt'
    del os.environ["HOME"]
    env['HOMEDRIVE'],env['HOMEPATH']=os.path.abspath("."),"DOES NOT EXIST"
    env["USERPROFILE"]=abspath(join(".","home_test_dir"))

    home_dir = genutils.get_home_dir()
    assert home_dir==abspath(join(".", "home_test_dir"))
    
    (env["HOME"],os.name,env['HOMEDRIVE'],env['HOMEPATH'])=oldstuff

def test_get_home_dir_9():
    """Testcase $HOME is not set, os=='nt' 
    env['HOMEDRIVE'],env['HOMEPATH'], env['USERPROFILE'] missing
    """
    import _winreg as wreg
    oldstuff = (env["HOME"],os.name,env['HOMEDRIVE'],
                env['HOMEPATH'],env["USERPROFILE"],
                wreg.OpenKey, wreg.QueryValueEx,
                )
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

    (env["HOME"],os.name,env['HOMEDRIVE'],
     env['HOMEPATH'],env["USERPROFILE"],
     wreg.OpenKey, wreg.QueryValueEx,) = oldstuff
     

def test_get_ipython_dir_1():
    """Testcase to see if we can call get_ipython_dir without Exceptions."""
    ipdir = genutils.get_ipython_dir()

def test_get_ipython_dir_2():
    """Testcase to see if we can call get_ipython_dir without Exceptions."""
    oldstuff = (env['IPYTHONDIR'],)

    env['IPYTHONDIR']="someplace/.ipython"
    ipdir = genutils.get_ipython_dir()
    assert ipdir == os.path.abspath("someplace/.ipython")

    (env['IPYTHONDIR'],)=oldstuff

class test_get_ipython_dir_3:
    @classmethod
    def setup_class(cls):
        cls.oldstuff = (env['IPYTHONDIR'], os.name, genutils.get_home_dir)
        del env['IPYTHONDIR']
        genutils.get_home_dir=lambda : "someplace"

    @classmethod
    def teardown_class(cls):
        (env['IPYTHONDIR'], os.name, genutils.get_home_dir)=cls.oldstuff
        
    def test_get_ipython_dir_a(self):
        """Testcase to see if we can call get_ipython_dir without Exceptions."""

        os.name="posix"
        ipdir = genutils.get_ipython_dir()
        assert ipdir == os.path.abspath(os.path.join("someplace", ".ipython"))
        
    def test_get_ipython_dir_b(self):
        """Testcase to see if we can call get_ipython_dir without Exceptions."""

        os.name="nt"
        ipdir = genutils.get_ipython_dir()
        assert ipdir == os.path.abspath(os.path.join("someplace", "_ipython"))
    
class test_get_security_dir:
    @classmethod
    def setup_class(cls):
        cls.oldstuff = (env['IPYTHONDIR'], os.name, genutils.get_home_dir)
        del env['IPYTHONDIR']
        genutils.get_home_dir=lambda : "someplace"

    @classmethod
    def teardown_class(cls):
        (env['IPYTHONDIR'], os.name, genutils.get_home_dir)=cls.oldstuff
        

    def test_get_security_dir():
        """Testcase to see if we can call get_security_dir without Exceptions."""
        sdir = genutils.get_security_dir()
    