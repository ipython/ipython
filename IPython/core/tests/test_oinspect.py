"""Tests for the object inspection functionality.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import os
import re

# Third-party imports
import nose.tools as nt

# Our own imports
from .. import oinspect
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic,
                                register_line_magic, register_cell_magic,
                                register_line_cell_magic)
from IPython.external.decorator import decorator
from IPython.utils import py3compat


#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

inspector = oinspect.Inspector()
ip = get_ipython()

#-----------------------------------------------------------------------------
# Local utilities
#-----------------------------------------------------------------------------

# WARNING: since this test checks the line number where a function is
# defined, if any code is inserted above, the following line will need to be
# updated.  Do NOT insert any whitespace between the next line and the function
# definition below.
THIS_LINE_NUMBER = 48  # Put here the actual number of this line
def test_find_source_lines():
    nt.assert_equal(oinspect.find_source_lines(test_find_source_lines), 
                    THIS_LINE_NUMBER+1)


# A couple of utilities to ensure these tests work the same from a source or a
# binary install
def pyfile(fname):
    return os.path.normcase(re.sub('.py[co]$', '.py', fname))


def match_pyfiles(f1, f2):
    nt.assert_equal(pyfile(f1), pyfile(f2))


def test_find_file():
    match_pyfiles(oinspect.find_file(test_find_file), os.path.abspath(__file__))


def test_find_file_decorated1():

    @decorator
    def noop1(f):
        def wrapper():
            return f(*a, **kw)
        return wrapper

    @noop1
    def f(x):
        "My docstring"
    
    match_pyfiles(oinspect.find_file(f), os.path.abspath(__file__))
    nt.assert_equal(f.__doc__, "My docstring")


def test_find_file_decorated2():

    @decorator
    def noop2(f, *a, **kw):
        return f(*a, **kw)

    @noop2
    def f(x):
        "My docstring 2"
    
    match_pyfiles(oinspect.find_file(f), os.path.abspath(__file__))
    nt.assert_equal(f.__doc__, "My docstring 2")
    

def test_find_file_magic():
    run = ip.find_line_magic('run')
    nt.assert_not_equal(oinspect.find_file(run), None)


# A few generic objects we can then inspect in the tests below

class Call(object):
    """This is the class docstring."""

    def __init__(self, x, y=1):
        """This is the constructor docstring."""

    def __call__(self, *a, **kw):
        """This is the call docstring."""

    def method(self, x, z=2):
        """Some method's docstring"""


class OldStyle:
    """An old-style class for testing."""
    pass


def f(x, y=2, *a, **kw):
    """A simple function."""


def g(y, z=3, *a, **kw):
    pass  # no docstring


@register_line_magic
def lmagic(line):
    "A line magic"


@register_cell_magic
def cmagic(line, cell):
    "A cell magic"


@register_line_cell_magic
def lcmagic(line, cell=None):
    "A line/cell magic"


@magics_class
class SimpleMagics(Magics):
    @line_magic
    def Clmagic(self, cline):
        "A class-based line magic"
        
    @cell_magic
    def Ccmagic(self, cline, ccell):
        "A class-based cell magic"
        
    @line_cell_magic
    def Clcmagic(self, cline, ccell=None):
        "A class-based line/cell magic"


class Awkward(object):
    def __getattr__(self, name):
        raise Exception(name)


def check_calltip(obj, name, call, docstring):
    """Generic check pattern all calltip tests will use"""
    info = inspector.info(obj, name)
    call_line, ds = oinspect.call_tip(info)
    nt.assert_equal(call_line, call)
    nt.assert_equal(ds, docstring)

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_calltip_class():
    check_calltip(Call, 'Call', 'Call(x, y=1)', Call.__init__.__doc__)


def test_calltip_instance():
    c = Call(1)
    check_calltip(c, 'c', 'c(*a, **kw)', c.__call__.__doc__)


def test_calltip_method():
    c = Call(1)
    check_calltip(c.method, 'c.method', 'c.method(x, z=2)', c.method.__doc__)


def test_calltip_function():
    check_calltip(f, 'f', 'f(x, y=2, *a, **kw)', f.__doc__)


def test_calltip_function2():
    check_calltip(g, 'g', 'g(y, z=3, *a, **kw)', '<no docstring>')


def test_calltip_builtin():
    check_calltip(sum, 'sum', None, sum.__doc__)


def test_calltip_line_magic():
    check_calltip(lmagic, 'lmagic', 'lmagic(line)', "A line magic")

        
def test_calltip_cell_magic():
    check_calltip(cmagic, 'cmagic', 'cmagic(line, cell)', "A cell magic")

        
def test_calltip_line_magic():
    check_calltip(lcmagic, 'lcmagic', 'lcmagic(line, cell=None)', 
                  "A line/cell magic")
        

def test_class_magics():
    cm = SimpleMagics(ip)
    ip.register_magics(cm)
    check_calltip(cm.Clmagic, 'Clmagic', 'Clmagic(cline)',
                  "A class-based line magic")
    check_calltip(cm.Ccmagic, 'Ccmagic', 'Ccmagic(cline, ccell)',
                  "A class-based cell magic")
    check_calltip(cm.Clcmagic, 'Clcmagic', 'Clcmagic(cline, ccell=None)',
                  "A class-based line/cell magic")
    

def test_info():
    "Check that Inspector.info fills out various fields as expected."
    i = inspector.info(Call, oname='Call')
    nt.assert_equal(i['type_name'], 'type')
    expted_class = str(type(type))  # <class 'type'> (Python 3) or <type 'type'>
    nt.assert_equal(i['base_class'], expted_class)
    nt.assert_equal(i['string_form'], "<class 'IPython.core.tests.test_oinspect.Call'>")
    fname = __file__
    if fname.endswith(".pyc"):
        fname = fname[:-1]
    # case-insensitive comparison needed on some filesystems
    # e.g. Windows:
    nt.assert_equal(i['file'].lower(), fname.lower())
    nt.assert_equal(i['definition'], 'Call(self, *a, **kw)\n')
    nt.assert_equal(i['docstring'], Call.__doc__)
    nt.assert_equal(i['source'], None)
    nt.assert_true(i['isclass'])
    nt.assert_equal(i['init_definition'], "Call(self, x, y=1)\n")
    nt.assert_equal(i['init_docstring'], Call.__init__.__doc__)

    i = inspector.info(Call, detail_level=1)
    nt.assert_not_equal(i['source'], None)
    nt.assert_equal(i['docstring'], None)

    c = Call(1)
    c.__doc__ = "Modified instance docstring"
    i = inspector.info(c)
    nt.assert_equal(i['type_name'], 'Call')
    nt.assert_equal(i['docstring'], "Modified instance docstring")
    nt.assert_equal(i['class_docstring'], Call.__doc__)
    nt.assert_equal(i['init_docstring'], Call.__init__.__doc__)
    nt.assert_equal(i['call_docstring'], c.__call__.__doc__)

    # Test old-style classes, which for example may not have an __init__ method.
    if not py3compat.PY3:
        i = inspector.info(OldStyle)
        nt.assert_equal(i['type_name'], 'classobj')

        i = inspector.info(OldStyle())
        nt.assert_equal(i['type_name'], 'instance')
        nt.assert_equal(i['docstring'], OldStyle.__doc__)

def test_info_awkward():
    # Just test that this doesn't throw an error.
    i = inspector.info(Awkward())

def test_getdoc():
    class A(object):
        """standard docstring"""
        pass
    
    class B(object):
        """standard docstring"""
        def getdoc(self):
            return "custom docstring"
    
    class C(object):
        """standard docstring"""
        def getdoc(self):
            return None
    
    a = A()
    b = B()
    c = C()
    
    nt.assert_equal(oinspect.getdoc(a), "standard docstring")
    nt.assert_equal(oinspect.getdoc(b), "custom docstring")
    nt.assert_equal(oinspect.getdoc(c), "standard docstring")

def test_pdef():
    # See gh-1914
    def foo(): pass
    inspector.pdef(foo, 'foo')
