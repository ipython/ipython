"""Tests for the Formatters.
"""

from math import pi

try:
    import numpy
except:
    numpy = None
import nose.tools as nt

from IPython.core.formatters import PlainTextFormatter, _mod_name_key

class A(object):
    def __repr__(self):
        return 'A()'

class B(A):
    def __repr__(self):
        return 'B()'

class C:
    pass

class BadPretty(object):
    _repr_pretty_ = None

class GoodPretty(object):
    def _repr_pretty_(self, pp, cycle):
        pp.text('foo')

    def __repr__(self):
        return 'GoodPretty()'

def foo_printer(obj, pp, cycle):
    pp.text('foo')

def test_pretty():
    f = PlainTextFormatter()
    f.for_type(A, foo_printer)
    nt.assert_equal(f(A()), 'foo')
    nt.assert_equal(f(B()), 'foo')
    nt.assert_equal(f(GoodPretty()), 'foo')
    # Just don't raise an exception for the following:
    f(BadPretty())

    f.pprint = False
    nt.assert_equal(f(A()), 'A()')
    nt.assert_equal(f(B()), 'B()')
    nt.assert_equal(f(GoodPretty()), 'GoodPretty()')


def test_deferred():
    f = PlainTextFormatter()

def test_precision():
    """test various values for float_precision."""
    f = PlainTextFormatter()
    nt.assert_equal(f(pi), repr(pi))
    f.float_precision = 0
    if numpy:
        po = numpy.get_printoptions()
        nt.assert_equal(po['precision'], 0)
    nt.assert_equal(f(pi), '3')
    f.float_precision = 2
    if numpy:
        po = numpy.get_printoptions()
        nt.assert_equal(po['precision'], 2)
    nt.assert_equal(f(pi), '3.14')
    f.float_precision = '%g'
    if numpy:
        po = numpy.get_printoptions()
        nt.assert_equal(po['precision'], 2)
    nt.assert_equal(f(pi), '3.14159')
    f.float_precision = '%e'
    nt.assert_equal(f(pi), '3.141593e+00')
    f.float_precision = ''
    if numpy:
        po = numpy.get_printoptions()
        nt.assert_equal(po['precision'], 8)
    nt.assert_equal(f(pi), repr(pi))

def test_bad_precision():
    """test various invalid values for float_precision."""
    f = PlainTextFormatter()
    def set_fp(p):
        f.float_precision=p
    nt.assert_raises(ValueError, set_fp, '%')
    nt.assert_raises(ValueError, set_fp, '%.3f%i')
    nt.assert_raises(ValueError, set_fp, 'foo')
    nt.assert_raises(ValueError, set_fp, -1)


def test_for_type():
    f = PlainTextFormatter()
    
    # initial return is None
    assert f.for_type(C, foo_printer) is None
    # no func queries
    assert f.for_type(C) is foo_printer
    # shouldn't change anything
    assert f.for_type(C) is foo_printer
    # None should do the same
    assert f.for_type(C, None) is foo_printer
    assert f.for_type(C, None) is foo_printer


def test_for_type_string():
    f = PlainTextFormatter()
    
    mod = C.__module__
    
    type_str = '%s.%s' % (C.__module__, 'C')
    
    # initial return is None
    assert f.for_type(type_str, foo_printer) is None
    # no func queries
    assert f.for_type(type_str) is foo_printer
    assert _mod_name_key(C) in f.deferred_printers
    assert f.for_type(C) is foo_printer
    assert _mod_name_key(C) not in f.deferred_printers
    assert C in f.type_printers


def test_for_type_by_name():
    f = PlainTextFormatter()
    
    mod = C.__module__
    
    # initial return is None
    assert f.for_type_by_name(mod, 'C', foo_printer) is None
    # no func queries
    assert f.for_type_by_name(mod, 'C') is foo_printer
    # shouldn't change anything
    assert f.for_type_by_name(mod, 'C') is foo_printer
    # None should do the same
    assert f.for_type_by_name(mod, 'C', None) is foo_printer
    assert f.for_type_by_name(mod, 'C', None) is foo_printer


def test_lookup():
    f = PlainTextFormatter()
    
    mod = C.__module__
    c = C()
    
    type_str = '%s.%s' % (C.__module__, 'C')
    
    # initial return is None
    assert f.for_type(type_str, foo_printer) is None
    # no func queries
    assert f.lookup(c) is foo_printer

