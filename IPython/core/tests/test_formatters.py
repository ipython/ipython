"""Tests for the Formatters."""

from math import pi

try:
    import numpy
except:
    numpy = None
import nose.tools as nt

from IPython.config import Config
from IPython.core.formatters import (
    PlainTextFormatter, HTMLFormatter, PDFFormatter, _mod_name_key
)
from IPython.utils.io import capture_output

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
    
    # initial return, None
    nt.assert_is(f.for_type(C, foo_printer), None)
    # no func queries
    nt.assert_is(f.for_type(C), foo_printer)
    # shouldn't change anything
    nt.assert_is(f.for_type(C), foo_printer)
    # None should do the same
    nt.assert_is(f.for_type(C, None), foo_printer)
    nt.assert_is(f.for_type(C, None), foo_printer)

def test_for_type_string():
    f = PlainTextFormatter()
    
    mod = C.__module__
    
    type_str = '%s.%s' % (C.__module__, 'C')
    
    # initial return, None
    nt.assert_is(f.for_type(type_str, foo_printer), None)
    # no func queries
    nt.assert_is(f.for_type(type_str), foo_printer)
    nt.assert_in(_mod_name_key(C), f.deferred_printers)
    nt.assert_is(f.for_type(C), foo_printer)
    nt.assert_not_in(_mod_name_key(C), f.deferred_printers)
    nt.assert_in(C, f.type_printers)

def test_for_type_by_name():
    f = PlainTextFormatter()
    
    mod = C.__module__
    
    # initial return, None
    nt.assert_is(f.for_type_by_name(mod, 'C', foo_printer), None)
    # no func queries
    nt.assert_is(f.for_type_by_name(mod, 'C'), foo_printer)
    # shouldn't change anything
    nt.assert_is(f.for_type_by_name(mod, 'C'), foo_printer)
    # None should do the same
    nt.assert_is(f.for_type_by_name(mod, 'C', None), foo_printer)
    nt.assert_is(f.for_type_by_name(mod, 'C', None), foo_printer)

def test_lookup():
    f = PlainTextFormatter()
    
    f.for_type(C, foo_printer)
    nt.assert_is(f.lookup(C()), foo_printer)
    with nt.assert_raises(KeyError):
        f.lookup(A())

def test_lookup_string():
    f = PlainTextFormatter()
    type_str = '%s.%s' % (C.__module__, 'C')
    
    f.for_type(type_str, foo_printer)
    nt.assert_is(f.lookup(C()), foo_printer)
    # should move from deferred to imported dict
    nt.assert_not_in(_mod_name_key(C), f.deferred_printers)
    nt.assert_in(C, f.type_printers)

def test_lookup_by_type():
    f = PlainTextFormatter()
    f.for_type(C, foo_printer)
    nt.assert_is(f.lookup_by_type(C), foo_printer)
    type_str = '%s.%s' % (C.__module__, 'C')
    with nt.assert_raises(KeyError):
        f.lookup_by_type(A)

def test_lookup_by_type_string():
    f = PlainTextFormatter()
    type_str = '%s.%s' % (C.__module__, 'C')
    f.for_type(type_str, foo_printer)
    
    # verify insertion
    nt.assert_in(_mod_name_key(C), f.deferred_printers)
    nt.assert_not_in(C, f.type_printers)
    
    nt.assert_is(f.lookup_by_type(type_str), foo_printer)
    # lookup by string doesn't cause import
    nt.assert_in(_mod_name_key(C), f.deferred_printers)
    nt.assert_not_in(C, f.type_printers)
    
    nt.assert_is(f.lookup_by_type(C), foo_printer)
    # should move from deferred to imported dict
    nt.assert_not_in(_mod_name_key(C), f.deferred_printers)
    nt.assert_in(C, f.type_printers)

def test_in_formatter():
    f = PlainTextFormatter()
    f.for_type(C, foo_printer)
    type_str = '%s.%s' % (C.__module__, 'C')
    nt.assert_in(C, f)
    nt.assert_in(type_str, f)

def test_string_in_formatter():
    f = PlainTextFormatter()
    type_str = '%s.%s' % (C.__module__, 'C')
    f.for_type(type_str, foo_printer)
    nt.assert_in(type_str, f)
    nt.assert_in(C, f)

def test_pop():
    f = PlainTextFormatter()
    f.for_type(C, foo_printer)
    nt.assert_is(f.lookup_by_type(C), foo_printer)
    nt.assert_is(f.pop(C, None), foo_printer)
    f.for_type(C, foo_printer)
    nt.assert_is(f.pop(C), foo_printer)
    with nt.assert_raises(KeyError):
        f.lookup_by_type(C)
    with nt.assert_raises(KeyError):
        f.pop(C)
    with nt.assert_raises(KeyError):
        f.pop(A)
    nt.assert_is(f.pop(A, None), None)

def test_pop_string():
    f = PlainTextFormatter()
    type_str = '%s.%s' % (C.__module__, 'C')
    
    with nt.assert_raises(KeyError):
        f.pop(type_str)
    
    f.for_type(type_str, foo_printer)
    f.pop(type_str)
    with nt.assert_raises(KeyError):
        f.lookup_by_type(C)
    with nt.assert_raises(KeyError):
        f.pop(type_str)

    f.for_type(C, foo_printer)
    nt.assert_is(f.pop(type_str, None), foo_printer)
    with nt.assert_raises(KeyError):
        f.lookup_by_type(C)
    with nt.assert_raises(KeyError):
        f.pop(type_str)
    nt.assert_is(f.pop(type_str, None), None)
    

def test_warn_error_method():
    f = HTMLFormatter()
    class BadHTML(object):
        def _repr_html_(self):
            return 1/0
    bad = BadHTML()
    with capture_output() as captured:
        result = f(bad)
    nt.assert_is(result, None)
    nt.assert_in("FormatterWarning", captured.stderr)
    nt.assert_in("text/html", captured.stderr)
    nt.assert_in("zero", captured.stderr)

def test_nowarn_notimplemented():
    f = HTMLFormatter()
    class HTMLNotImplemented(object):
        def _repr_html_(self):
            raise NotImplementedError
            return 1/0
    h = HTMLNotImplemented()
    with capture_output() as captured:
        result = f(h)
    nt.assert_is(result, None)
    nt.assert_not_in("FormatterWarning", captured.stderr)

def test_warn_error_for_type():
    f = HTMLFormatter()
    f.for_type(int, lambda i: name_error)
    with capture_output() as captured:
        result = f(5)
    nt.assert_is(result, None)
    nt.assert_in("FormatterWarning", captured.stderr)
    nt.assert_in("text/html", captured.stderr)
    nt.assert_in("name_error", captured.stderr)

def test_warn_error_pretty_method():
    f = PlainTextFormatter()
    class BadPretty(object):
        def _repr_pretty_(self):
            return "hello"
    bad = BadPretty()
    with capture_output() as captured:
        result = f(bad)
    nt.assert_is(result, None)
    nt.assert_in("FormatterWarning", captured.stderr)
    nt.assert_in("text/plain", captured.stderr)
    nt.assert_in("argument", captured.stderr)

class MakePDF(object):
    def _repr_pdf_(self):
        return 'PDF'

def test_pdf_formatter():
    pdf = MakePDF()
    f = PDFFormatter()
    nt.assert_equal(f(pdf), 'PDF')

def test_print_method_bound():
    f = HTMLFormatter()
    class MyHTML(object):
        def _repr_html_(self):
            return "hello"

    with capture_output() as captured:
        result = f(MyHTML)
    nt.assert_is(result, None)
    nt.assert_not_in("FormatterWarning", captured.stderr)

    with capture_output() as captured:
        result = f(MyHTML())
    nt.assert_equal(result, "hello")
    nt.assert_equal(captured.stderr, "")

def test_format_config():
    """config objects don't pretend to support fancy reprs with lazy attrs"""
    f = HTMLFormatter()
    cfg = Config()
    with capture_output() as captured:
        result = f(cfg)
    nt.assert_is(result, None)
    nt.assert_equal(captured.stderr, "")

    with capture_output() as captured:
        result = f(Config)
    nt.assert_is(result, None)
    nt.assert_equal(captured.stderr, "")
