# coding: utf-8
"""Tests for IPython.lib.pretty."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import nose.tools as nt

from IPython.lib import pretty
from IPython.testing.decorators import skip_without
from IPython.utils.py3compat import PY3, unicode_to_str

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO


class MyList(object):
    def __init__(self, content):
        self.content = content
    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text("MyList(...)")
        else:
            with p.group(3, "MyList(", ")"):
                for (i, child) in enumerate(self.content):
                    if i:
                        p.text(",")
                        p.breakable()
                    else:
                        p.breakable("")
                    p.pretty(child)


class MyDict(dict):
    def _repr_pretty_(self, p, cycle):
        p.text("MyDict(...)")

class MyObj(object):
    def somemethod(self):
        pass


class Dummy1(object):
    def _repr_pretty_(self, p, cycle):
        p.text("Dummy1(...)")

class Dummy2(Dummy1):
    _repr_pretty_ = None

class NoModule(object):
    pass

NoModule.__module__ = None

class Breaking(object):
    def _repr_pretty_(self, p, cycle):
        with p.group(4,"TG: ",":"):
            p.text("Breaking(")
            p.break_()
            p.text(")")

class BreakingRepr(object):
    def __repr__(self):
        return "Breaking(\n)"

class BreakingReprParent(object):
    def _repr_pretty_(self, p, cycle):
        with p.group(4,"TG: ",":"):
            p.pretty(BreakingRepr())

class BadRepr(object):
    
    def __repr__(self):
        return 1/0


def test_indentation():
    """Test correct indentation in groups"""
    count = 40
    gotoutput = pretty.pretty(MyList(range(count)))
    expectedoutput = "MyList(\n" + ",\n".join("   %d" % i for i in range(count)) + ")"

    nt.assert_equal(gotoutput, expectedoutput)


def test_dispatch():
    """
    Test correct dispatching: The _repr_pretty_ method for MyDict
    must be found before the registered printer for dict.
    """
    gotoutput = pretty.pretty(MyDict())
    expectedoutput = "MyDict(...)"

    nt.assert_equal(gotoutput, expectedoutput)


def test_callability_checking():
    """
    Test that the _repr_pretty_ method is tested for callability and skipped if
    not.
    """
    gotoutput = pretty.pretty(Dummy2())
    expectedoutput = "Dummy1(...)"

    nt.assert_equal(gotoutput, expectedoutput)


def test_sets():
    """
    Test that set and frozenset use Python 3 formatting.
    """
    objects = [set(), frozenset(), set([1]), frozenset([1]), set([1, 2]),
        frozenset([1, 2]), set([-1, -2, -3])]
    expected = ['set()', 'frozenset()', '{1}', 'frozenset({1})', '{1, 2}',
        'frozenset({1, 2})', '{-3, -2, -1}']
    for obj, expected_output in zip(objects, expected):
        got_output = pretty.pretty(obj)
        yield nt.assert_equal, got_output, expected_output


@skip_without('xxlimited')
def test_pprint_heap_allocated_type():
    """
    Test that pprint works for heap allocated types.
    """
    import xxlimited
    output = pretty.pretty(xxlimited.Null)
    nt.assert_equal(output, 'xxlimited.Null')

def test_pprint_nomod():
    """
    Test that pprint works for classes with no __module__.
    """
    output = pretty.pretty(NoModule)
    nt.assert_equal(output, 'NoModule')
    
def test_pprint_break():
    """
    Test that p.break_ produces expected output
    """
    output = pretty.pretty(Breaking())
    expected = "TG: Breaking(\n    ):"
    nt.assert_equal(output, expected)

def test_pprint_break_repr():
    """
    Test that p.break_ is used in repr
    """
    output = pretty.pretty(BreakingReprParent())
    expected = "TG: Breaking(\n    ):"
    nt.assert_equal(output, expected)

def test_bad_repr():
    """Don't catch bad repr errors"""
    with nt.assert_raises(ZeroDivisionError):
        output = pretty.pretty(BadRepr())

class BadException(Exception):
    def __str__(self):
        return -1

class ReallyBadRepr(object):
    __module__ = 1
    @property
    def __class__(self):
        raise ValueError("I am horrible")
    
    def __repr__(self):
        raise BadException()

def test_really_bad_repr():
    with nt.assert_raises(BadException):
        output = pretty.pretty(ReallyBadRepr())


class SA(object):
    pass

class SB(SA):
    pass

def test_super_repr():
    output = pretty.pretty(super(SA))
    nt.assert_in("SA", output)

    sb = SB()
    output = pretty.pretty(super(SA, sb))
    nt.assert_in("SA", output)


def test_long_list():
    lis = list(range(10000))
    p = pretty.pretty(lis)
    last2 = p.rsplit('\n', 2)[-2:]
    nt.assert_equal(last2, [' 999,', ' ...]'])

def test_long_set():
    s = set(range(10000))
    p = pretty.pretty(s)
    last2 = p.rsplit('\n', 2)[-2:]
    nt.assert_equal(last2, [' 999,', ' ...}'])

def test_long_tuple():
    tup = tuple(range(10000))
    p = pretty.pretty(tup)
    last2 = p.rsplit('\n', 2)[-2:]
    nt.assert_equal(last2, [' 999,', ' ...)'])

def test_long_dict():
    d = { n:n for n in range(10000) }
    p = pretty.pretty(d)
    last2 = p.rsplit('\n', 2)[-2:]
    nt.assert_equal(last2, [' 999: 999,', ' ...}'])

def test_unbound_method():
    output = pretty.pretty(MyObj.somemethod)
    nt.assert_in('MyObj.somemethod', output)


class MetaClass(type):
    def __new__(cls, name):
        return type.__new__(cls, name, (object,), {'name': name})

    def __repr__(self):
        return "[CUSTOM REPR FOR CLASS %s]" % self.name


ClassWithMeta = MetaClass('ClassWithMeta')


def test_metaclass_repr():
    output = pretty.pretty(ClassWithMeta)
    nt.assert_equal(output, "[CUSTOM REPR FOR CLASS ClassWithMeta]")


def test_unicode_repr():
    u = u"üniçodé"
    ustr = unicode_to_str(u)
    
    class C(object):
        def __repr__(self):
            return ustr
    
    c = C()
    p = pretty.pretty(c)
    nt.assert_equal(p, u)
    p = pretty.pretty([c])
    nt.assert_equal(p, u'[%s]' % u)


def test_basic_class():
    def type_pprint_wrapper(obj, p, cycle):
        if obj is MyObj:
            type_pprint_wrapper.called = True
        return pretty._type_pprint(obj, p, cycle)
    type_pprint_wrapper.called = False

    stream = StringIO()
    printer = pretty.RepresentationPrinter(stream)
    printer.type_pprinters[type] = type_pprint_wrapper
    printer.pretty(MyObj)
    printer.flush()
    output = stream.getvalue()

    nt.assert_equal(output, '%s.MyObj' % __name__)
    nt.assert_true(type_pprint_wrapper.called)
