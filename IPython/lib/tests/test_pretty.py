# coding: utf-8
"""Tests for IPython.lib.pretty."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

from collections import Counter, defaultdict, deque, OrderedDict

import nose.tools as nt

from IPython.lib import pretty
from IPython.testing.decorators import skip_without, py2_only
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


# This is only run on Python 2 because in Python 3 the language prevents you
# from setting a non-unicode value for __qualname__ on a metaclass, and it
# doesn't respect the descriptor protocol if you subclass unicode and implement
# __get__.
@py2_only
def test_fallback_to__name__on_type():
    # Test that we correctly repr types that have non-string values for
    # __qualname__ by falling back to __name__

    class Type(object):
        __qualname__ = 5

    # Test repring of the type.
    stream = StringIO()
    printer = pretty.RepresentationPrinter(stream)

    printer.pretty(Type)
    printer.flush()
    output = stream.getvalue()

    # If __qualname__ is malformed, we should fall back to __name__.
    expected = '.'.join([__name__, Type.__name__])
    nt.assert_equal(output, expected)

    # Clear stream buffer.
    stream.buf = ''

    # Test repring of an instance of the type.
    instance = Type()
    printer.pretty(instance)
    printer.flush()
    output = stream.getvalue()

    # Should look like:
    # <IPython.lib.tests.test_pretty.Type at 0x7f7658ae07d0>
    prefix = '<' + '.'.join([__name__, Type.__name__]) + ' at 0x'
    nt.assert_true(output.startswith(prefix))


@py2_only
def test_fail_gracefully_on_bogus__qualname__and__name__():
    # Test that we correctly repr types that have non-string values for both
    # __qualname__ and __name__

    class Meta(type):
        __name__ = 5

    class Type(object):
        __metaclass__ = Meta
        __qualname__ = 5

    stream = StringIO()
    printer = pretty.RepresentationPrinter(stream)

    printer.pretty(Type)
    printer.flush()
    output = stream.getvalue()

    # If we can't find __name__ or __qualname__ just use a sentinel string.
    expected = '.'.join([__name__, '<unknown type>'])
    nt.assert_equal(output, expected)

    # Clear stream buffer.
    stream.buf = ''

    # Test repring of an instance of the type.
    instance = Type()
    printer.pretty(instance)
    printer.flush()
    output = stream.getvalue()

    # Should look like:
    # <IPython.lib.tests.test_pretty.<unknown type> at 0x7f7658ae07d0>
    prefix = '<' + '.'.join([__name__, '<unknown type>']) + ' at 0x'
    nt.assert_true(output.startswith(prefix))


def test_collections_defaultdict():
    # Create defaultdicts with cycles
    a = defaultdict()
    a.default_factory = a
    b = defaultdict(list)
    b['key'] = b

    # Dictionary order cannot be relied on, test against single keys.
    cases = [
        (defaultdict(list), 'defaultdict(list, {})'),
        (defaultdict(list, {'key': '-' * 50}),
         "defaultdict(list,\n"
         "            {'key': '--------------------------------------------------'})"),
        (a, 'defaultdict(defaultdict(...), {})'),
        (b, "defaultdict(list, {'key': defaultdict(...)})"),
    ]
    for obj, expected in cases:
        nt.assert_equal(pretty.pretty(obj), expected)


def test_collections_ordereddict():
    # Create OrderedDict with cycle
    a = OrderedDict()
    a['key'] = a

    cases = [
        (OrderedDict(), 'OrderedDict()'),
        (OrderedDict((i, i) for i in range(1000, 1010)),
         'OrderedDict([(1000, 1000),\n'
         '             (1001, 1001),\n'
         '             (1002, 1002),\n'
         '             (1003, 1003),\n'
         '             (1004, 1004),\n'
         '             (1005, 1005),\n'
         '             (1006, 1006),\n'
         '             (1007, 1007),\n'
         '             (1008, 1008),\n'
         '             (1009, 1009)])'),
        (a, "OrderedDict([('key', OrderedDict(...))])"),
    ]
    for obj, expected in cases:
        nt.assert_equal(pretty.pretty(obj), expected)


def test_collections_deque():
    # Create deque with cycle
    a = deque()
    a.append(a)

    cases = [
        (deque(), 'deque([])'),
        (deque(i for i in range(1000, 1020)),
         'deque([1000,\n'
         '       1001,\n'
         '       1002,\n'
         '       1003,\n'
         '       1004,\n'
         '       1005,\n'
         '       1006,\n'
         '       1007,\n'
         '       1008,\n'
         '       1009,\n'
         '       1010,\n'
         '       1011,\n'
         '       1012,\n'
         '       1013,\n'
         '       1014,\n'
         '       1015,\n'
         '       1016,\n'
         '       1017,\n'
         '       1018,\n'
         '       1019])'),
        (a, 'deque([deque(...)])'),
    ]
    for obj, expected in cases:
        nt.assert_equal(pretty.pretty(obj), expected)

def test_collections_counter():
    class MyCounter(Counter):
        pass
    cases = [
        (Counter(), 'Counter()'),
        (Counter(a=1), "Counter({'a': 1})"),
        (MyCounter(a=1), "MyCounter({'a': 1})"),
    ]
    for obj, expected in cases:
        nt.assert_equal(pretty.pretty(obj), expected)
