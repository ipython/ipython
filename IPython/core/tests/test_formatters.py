"""Tests for the Formatters.
"""

import nose.tools as nt

from IPython.core.formatters import FormatterABC, DefaultFormatter

class A(object):
    def __repr__(self):
        return 'A()'

class B(A):
    def __repr__(self):
        return 'B()'

def foo_printer(obj, pp, cycle):
    pp.text('foo')

def test_pretty():
    f = DefaultFormatter()
    f.for_type(A, foo_printer)
    nt.assert_equals(f(A()), 'foo')
    nt.assert_equals(f(B()), 'foo')
    f.pprint = False
    nt.assert_equals(f(A()), 'A()')
    nt.assert_equals(f(B()), 'B()')

def test_deferred():
    f = DefaultFormatter()

