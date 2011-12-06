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

# Third-party imports
import nose.tools as nt

# Our own imports
from .. import oinspect
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

inspector = oinspect.Inspector()

#-----------------------------------------------------------------------------
# Local utilities
#-----------------------------------------------------------------------------

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
