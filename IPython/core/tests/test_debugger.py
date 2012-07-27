"""Tests for debugging machinery.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys

# third-party
import nose.tools as nt

# Our own
from IPython.core import debugger

#-----------------------------------------------------------------------------
# Helper classes, from CPython's Pdb test suite
#-----------------------------------------------------------------------------

class _FakeInput(object):
    """
    A fake input stream for pdb's interactive debugger.  Whenever a
    line is read, print it (to simulate the user typing it), and then
    return it.  The set of lines to return is specified in the
    constructor; they should not have trailing newlines.
    """
    def __init__(self, lines):
        self.lines = iter(lines)

    def readline(self):
        line = next(self.lines)
        print line
        return line+'\n'

class PdbTestInput(object):
    """Context manager that makes testing Pdb in doctests easier."""

    def __init__(self, input):
        self.input = input

    def __enter__(self):
        self.real_stdin = sys.stdin
        sys.stdin = _FakeInput(self.input)

    def __exit__(self, *exc):
        sys.stdin = self.real_stdin

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_longer_repr():
    from repr import repr as trepr
    
    a = '1234567890'* 7
    ar = "'1234567890123456789012345678901234567890123456789012345678901234567890'"
    a_trunc = "'123456789012...8901234567890'"
    nt.assert_equals(trepr(a), a_trunc)
    # The creation of our tracer modifies the repr module's repr function
    # in-place, since that global is used directly by the stdlib's pdb module.
    t = debugger.Tracer()
    nt.assert_equals(trepr(a), ar)

def test_ipdb_magics():
    '''Test calling some IPython magics from ipdb.

    First, set up some test functions and classes which we can inspect.

    >>> class ExampleClass(object):
    ...    """Docstring for ExampleClass."""
    ...    def __init__(self):
    ...        """Docstring for ExampleClass.__init__"""
    ...        pass
    ...    def __str__(self):
    ...        return "ExampleClass()"

    >>> def example_function(x, y, z="hello"):
    ...     """Docstring for example_function."""
    ...     pass

    Create a function which triggers ipdb.

    >>> def trigger_ipdb():
    ...    a = ExampleClass()
    ...    debugger.Pdb().set_trace()

    >>> with PdbTestInput([
    ...    'pdef example_function',
    ...    'pdoc ExampleClass',
    ...    'pinfo a',
    ...    'continue',
    ... ]):
    ...     trigger_ipdb()
    --Return--
    None
    > <doctest ...>(3)trigger_ipdb()
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> pdef example_function
     example_function(x, y, z='hello')
     ipdb> pdoc ExampleClass
    Class Docstring:
        Docstring for ExampleClass.
    Constructor Docstring:
        Docstring for ExampleClass.__init__
    ipdb> pinfo a
    Type:       ExampleClass
    String Form:ExampleClass()
    Namespace:  Locals
    File:       ...
    Docstring:  Docstring for ExampleClass.
    Constructor Docstring:Docstring for ExampleClass.__init__
    ipdb> continue
    '''
