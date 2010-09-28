"""Tests for the object inspection functionality.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010 The IPython Development Team.
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
