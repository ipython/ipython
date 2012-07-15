# encoding: utf-8
"""
Tests for IPython.utils.traitlets.

Authors:

* Brian Granger
* Enthought, Inc.  Some of the code in this file comes from enthought.traits
  and is licensed under the BSD license.  Also, many of the ideas also come
  from enthought.traits even though our implementation is very different.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import re
import sys
from unittest import TestCase

from nose import SkipTest

from IPython.utils.traitlets import (
    HasTraits, MetaHasTraits, TraitType, Any, CBytes,
    Int, Long, Integer, Float, Complex, Bytes, Unicode, TraitError,
    Undefined, Type, This, Instance, TCPAddress, List, Tuple,
    ObjectName, DottedObjectName, CRegExp
)
from IPython.utils import py3compat
from IPython.testing.decorators import skipif

#-----------------------------------------------------------------------------
# Helper classes for testing
#-----------------------------------------------------------------------------


class HasTraitsStub(HasTraits):

    def _notify_trait(self, name, old, new):
        self._notify_name = name
        self._notify_old = old
        self._notify_new = new


#-----------------------------------------------------------------------------
# Test classes
#-----------------------------------------------------------------------------


class TestTraitType(TestCase):

    def test_get_undefined(self):
        class A(HasTraits):
            a = TraitType
        a = A()
        self.assertEquals(a.a, Undefined)

    def test_set(self):
        class A(HasTraitsStub):
            a = TraitType

        a = A()
        a.a = 10
        self.assertEquals(a.a, 10)
        self.assertEquals(a._notify_name, 'a')
        self.assertEquals(a._notify_old, Undefined)
        self.assertEquals(a._notify_new, 10)

    def test_validate(self):
        class MyTT(TraitType):
            def validate(self, inst, value):
                return -1
        class A(HasTraitsStub):
            tt = MyTT

        a = A()
        a.tt = 10
        self.assertEquals(a.tt, -1)

    def test_default_validate(self):
        class MyIntTT(TraitType):
            def validate(self, obj, value):
                if isinstance(value, int):
                    return value
                self.error(obj, value)
        class A(HasTraits):
            tt = MyIntTT(10)
        a = A()
        self.assertEquals(a.tt, 10)

        # Defaults are validated when the HasTraits is instantiated
        class B(HasTraits):
            tt = MyIntTT('bad default')
        self.assertRaises(TraitError, B)

    def test_is_valid_for(self):
        class MyTT(TraitType):
            def is_valid_for(self, value):
                return True
        class A(HasTraits):
            tt = MyTT

        a = A()
        a.tt = 10
        self.assertEquals(a.tt, 10)

    def test_value_for(self):
        class MyTT(TraitType):
            def value_for(self, value):
                return 20
        class A(HasTraits):
            tt = MyTT

        a = A()
        a.tt = 10
        self.assertEquals(a.tt, 20)

    def test_info(self):
        class A(HasTraits):
            tt = TraitType
        a = A()
        self.assertEquals(A.tt.info(), 'any value')

    def test_error(self):
        class A(HasTraits):
            tt = TraitType
        a = A()
        self.assertRaises(TraitError, A.tt.error, a, 10)

    def test_dynamic_initializer(self):
        class A(HasTraits):
            x = Int(10)
            def _x_default(self):
                return 11
        class B(A):
            x = Int(20)
        class C(A):
            def _x_default(self):
                return 21

        a = A()
        self.assertEquals(a._trait_values, {})
        self.assertEquals(a._trait_dyn_inits.keys(), ['x'])
        self.assertEquals(a.x, 11)
        self.assertEquals(a._trait_values, {'x': 11})
        b = B()
        self.assertEquals(b._trait_values, {'x': 20})
        self.assertEquals(a._trait_dyn_inits.keys(), ['x'])
        self.assertEquals(b.x, 20)
        c = C()
        self.assertEquals(c._trait_values, {})
        self.assertEquals(a._trait_dyn_inits.keys(), ['x'])
        self.assertEquals(c.x, 21)
        self.assertEquals(c._trait_values, {'x': 21})
        # Ensure that the base class remains unmolested when the _default
        # initializer gets overridden in a subclass.
        a = A()
        c = C()
        self.assertEquals(a._trait_values, {})
        self.assertEquals(a._trait_dyn_inits.keys(), ['x'])
        self.assertEquals(a.x, 11)
        self.assertEquals(a._trait_values, {'x': 11})



class TestHasTraitsMeta(TestCase):

    def test_metaclass(self):
        self.assertEquals(type(HasTraits), MetaHasTraits)

        class A(HasTraits):
            a = Int

        a = A()
        self.assertEquals(type(a.__class__), MetaHasTraits)
        self.assertEquals(a.a,0)
        a.a = 10
        self.assertEquals(a.a,10)

        class B(HasTraits):
            b = Int()

        b = B()
        self.assertEquals(b.b,0)
        b.b = 10
        self.assertEquals(b.b,10)

        class C(HasTraits):
            c = Int(30)

        c = C()
        self.assertEquals(c.c,30)
        c.c = 10
        self.assertEquals(c.c,10)

    def test_this_class(self):
        class A(HasTraits):
            t = This()
            tt = This()
        class B(A):
            tt = This()
            ttt = This()
        self.assertEquals(A.t.this_class, A)
        self.assertEquals(B.t.this_class, A)
        self.assertEquals(B.tt.this_class, B)
        self.assertEquals(B.ttt.this_class, B)

class TestHasTraitsNotify(TestCase):

    def setUp(self):
        self._notify1 = []
        self._notify2 = []

    def notify1(self, name, old, new):
        self._notify1.append((name, old, new))

    def notify2(self, name, old, new):
        self._notify2.append((name, old, new))

    def test_notify_all(self):

        class A(HasTraits):
            a = Int
            b = Float

        a = A()
        a.on_trait_change(self.notify1)
        a.a = 0
        self.assertEquals(len(self._notify1),0)
        a.b = 0.0
        self.assertEquals(len(self._notify1),0)
        a.a = 10
        self.assert_(('a',0,10) in self._notify1)
        a.b = 10.0
        self.assert_(('b',0.0,10.0) in self._notify1)
        self.assertRaises(TraitError,setattr,a,'a','bad string')
        self.assertRaises(TraitError,setattr,a,'b','bad string')
        self._notify1 = []
        a.on_trait_change(self.notify1,remove=True)
        a.a = 20
        a.b = 20.0
        self.assertEquals(len(self._notify1),0)

    def test_notify_one(self):

        class A(HasTraits):
            a = Int
            b = Float

        a = A()
        a.on_trait_change(self.notify1, 'a')
        a.a = 0
        self.assertEquals(len(self._notify1),0)
        a.a = 10
        self.assert_(('a',0,10) in self._notify1)
        self.assertRaises(TraitError,setattr,a,'a','bad string')

    def test_subclass(self):

        class A(HasTraits):
            a = Int

        class B(A):
            b = Float

        b = B()
        self.assertEquals(b.a,0)
        self.assertEquals(b.b,0.0)
        b.a = 100
        b.b = 100.0
        self.assertEquals(b.a,100)
        self.assertEquals(b.b,100.0)

    def test_notify_subclass(self):

        class A(HasTraits):
            a = Int

        class B(A):
            b = Float

        b = B()
        b.on_trait_change(self.notify1, 'a')
        b.on_trait_change(self.notify2, 'b')
        b.a = 0
        b.b = 0.0
        self.assertEquals(len(self._notify1),0)
        self.assertEquals(len(self._notify2),0)
        b.a = 10
        b.b = 10.0
        self.assert_(('a',0,10) in self._notify1)
        self.assert_(('b',0.0,10.0) in self._notify2)

    def test_static_notify(self):

        class A(HasTraits):
            a = Int
            _notify1 = []
            def _a_changed(self, name, old, new):
                self._notify1.append((name, old, new))

        a = A()
        a.a = 0
        # This is broken!!!
        self.assertEquals(len(a._notify1),0)
        a.a = 10
        self.assert_(('a',0,10) in a._notify1)

        class B(A):
            b = Float
            _notify2 = []
            def _b_changed(self, name, old, new):
                self._notify2.append((name, old, new))

        b = B()
        b.a = 10
        b.b = 10.0
        self.assert_(('a',0,10) in b._notify1)
        self.assert_(('b',0.0,10.0) in b._notify2)

    def test_notify_args(self):

        def callback0():
            self.cb = ()
        def callback1(name):
            self.cb = (name,)
        def callback2(name, new):
            self.cb = (name, new)
        def callback3(name, old, new):
            self.cb = (name, old, new)

        class A(HasTraits):
            a = Int

        a = A()
        a.on_trait_change(callback0, 'a')
        a.a = 10
        self.assertEquals(self.cb,())
        a.on_trait_change(callback0, 'a', remove=True)

        a.on_trait_change(callback1, 'a')
        a.a = 100
        self.assertEquals(self.cb,('a',))
        a.on_trait_change(callback1, 'a', remove=True)

        a.on_trait_change(callback2, 'a')
        a.a = 1000
        self.assertEquals(self.cb,('a',1000))
        a.on_trait_change(callback2, 'a', remove=True)

        a.on_trait_change(callback3, 'a')
        a.a = 10000
        self.assertEquals(self.cb,('a',1000,10000))
        a.on_trait_change(callback3, 'a', remove=True)

        self.assertEquals(len(a._trait_notifiers['a']),0)


class TestHasTraits(TestCase):

    def test_trait_names(self):
        class A(HasTraits):
            i = Int
            f = Float
        a = A()
        self.assertEquals(sorted(a.trait_names()),['f','i'])
        self.assertEquals(sorted(A.class_trait_names()),['f','i'])

    def test_trait_metadata(self):
        class A(HasTraits):
            i = Int(config_key='MY_VALUE')
        a = A()
        self.assertEquals(a.trait_metadata('i','config_key'), 'MY_VALUE')

    def test_traits(self):
        class A(HasTraits):
            i = Int
            f = Float
        a = A()
        self.assertEquals(a.traits(), dict(i=A.i, f=A.f))
        self.assertEquals(A.class_traits(), dict(i=A.i, f=A.f))

    def test_traits_metadata(self):
        class A(HasTraits):
            i = Int(config_key='VALUE1', other_thing='VALUE2')
            f = Float(config_key='VALUE3', other_thing='VALUE2')
            j = Int(0)
        a = A()
        self.assertEquals(a.traits(), dict(i=A.i, f=A.f, j=A.j))
        traits = a.traits(config_key='VALUE1', other_thing='VALUE2')
        self.assertEquals(traits, dict(i=A.i))

        # This passes, but it shouldn't because I am replicating a bug in
        # traits.
        traits = a.traits(config_key=lambda v: True)
        self.assertEquals(traits, dict(i=A.i, f=A.f, j=A.j))

    def test_init(self):
        class A(HasTraits):
            i = Int()
            x = Float()
        a = A(i=1, x=10.0)
        self.assertEquals(a.i, 1)
        self.assertEquals(a.x, 10.0)

#-----------------------------------------------------------------------------
# Tests for specific trait types
#-----------------------------------------------------------------------------


class TestType(TestCase):

    def test_default(self):

        class B(object): pass
        class A(HasTraits):
            klass = Type

        a = A()
        self.assertEquals(a.klass, None)

        a.klass = B
        self.assertEquals(a.klass, B)
        self.assertRaises(TraitError, setattr, a, 'klass', 10)

    def test_value(self):

        class B(object): pass
        class C(object): pass
        class A(HasTraits):
            klass = Type(B)

        a = A()
        self.assertEquals(a.klass, B)
        self.assertRaises(TraitError, setattr, a, 'klass', C)
        self.assertRaises(TraitError, setattr, a, 'klass', object)
        a.klass = B

    def test_allow_none(self):

        class B(object): pass
        class C(B): pass
        class A(HasTraits):
            klass = Type(B, allow_none=False)

        a = A()
        self.assertEquals(a.klass, B)
        self.assertRaises(TraitError, setattr, a, 'klass', None)
        a.klass = C
        self.assertEquals(a.klass, C)

    def test_validate_klass(self):

        class A(HasTraits):
            klass = Type('no strings allowed')

        self.assertRaises(ImportError, A)

        class A(HasTraits):
            klass = Type('rub.adub.Duck')

        self.assertRaises(ImportError, A)

    def test_validate_default(self):

        class B(object): pass
        class A(HasTraits):
            klass = Type('bad default', B)

        self.assertRaises(ImportError, A)

        class C(HasTraits):
            klass = Type(None, B, allow_none=False)

        self.assertRaises(TraitError, C)

    def test_str_klass(self):

        class A(HasTraits):
            klass = Type('IPython.utils.ipstruct.Struct')

        from IPython.utils.ipstruct import Struct
        a = A()
        a.klass = Struct
        self.assertEquals(a.klass, Struct)

        self.assertRaises(TraitError, setattr, a, 'klass', 10)

class TestInstance(TestCase):

    def test_basic(self):
        class Foo(object): pass
        class Bar(Foo): pass
        class Bah(object): pass

        class A(HasTraits):
            inst = Instance(Foo)

        a = A()
        self.assert_(a.inst is None)
        a.inst = Foo()
        self.assert_(isinstance(a.inst, Foo))
        a.inst = Bar()
        self.assert_(isinstance(a.inst, Foo))
        self.assertRaises(TraitError, setattr, a, 'inst', Foo)
        self.assertRaises(TraitError, setattr, a, 'inst', Bar)
        self.assertRaises(TraitError, setattr, a, 'inst', Bah())

    def test_unique_default_value(self):
        class Foo(object): pass
        class A(HasTraits):
            inst = Instance(Foo,(),{})

        a = A()
        b = A()
        self.assert_(a.inst is not b.inst)

    def test_args_kw(self):
        class Foo(object):
            def __init__(self, c): self.c = c
        class Bar(object): pass
        class Bah(object):
            def __init__(self, c, d):
                self.c = c; self.d = d

        class A(HasTraits):
            inst = Instance(Foo, (10,))
        a = A()
        self.assertEquals(a.inst.c, 10)

        class B(HasTraits):
            inst = Instance(Bah, args=(10,), kw=dict(d=20))
        b = B()
        self.assertEquals(b.inst.c, 10)
        self.assertEquals(b.inst.d, 20)

        class C(HasTraits):
            inst = Instance(Foo)
        c = C()
        self.assert_(c.inst is None)

    def test_bad_default(self):
        class Foo(object): pass

        class A(HasTraits):
            inst = Instance(Foo, allow_none=False)

        self.assertRaises(TraitError, A)

    def test_instance(self):
        class Foo(object): pass

        def inner():
            class A(HasTraits):
                inst = Instance(Foo())

        self.assertRaises(TraitError, inner)


class TestThis(TestCase):

    def test_this_class(self):
        class Foo(HasTraits):
            this = This

        f = Foo()
        self.assertEquals(f.this, None)
        g = Foo()
        f.this = g
        self.assertEquals(f.this, g)
        self.assertRaises(TraitError, setattr, f, 'this', 10)

    def test_this_inst(self):
        class Foo(HasTraits):
            this = This()

        f = Foo()
        f.this = Foo()
        self.assert_(isinstance(f.this, Foo))

    def test_subclass(self):
        class Foo(HasTraits):
            t = This()
        class Bar(Foo):
            pass
        f = Foo()
        b = Bar()
        f.t = b
        b.t = f
        self.assertEquals(f.t, b)
        self.assertEquals(b.t, f)

    def test_subclass_override(self):
        class Foo(HasTraits):
            t = This()
        class Bar(Foo):
            t = This()
        f = Foo()
        b = Bar()
        f.t = b
        self.assertEquals(f.t, b)
        self.assertRaises(TraitError, setattr, b, 't', f)

class TraitTestBase(TestCase):
    """A best testing class for basic trait types."""

    def assign(self, value):
        self.obj.value = value

    def coerce(self, value):
        return value

    def test_good_values(self):
        if hasattr(self, '_good_values'):
            for value in self._good_values:
                self.assign(value)
                self.assertEquals(self.obj.value, self.coerce(value))

    def test_bad_values(self):
        if hasattr(self, '_bad_values'):
            for value in self._bad_values:
                try:
                    self.assertRaises(TraitError, self.assign, value)
                except AssertionError:
                    assert False, value

    def test_default_value(self):
        if hasattr(self, '_default_value'):
            self.assertEquals(self._default_value, self.obj.value)

    def tearDown(self):
        # restore default value after tests, if set
        if hasattr(self, '_default_value'):
            self.obj.value = self._default_value


class AnyTrait(HasTraits):

    value = Any

class AnyTraitTest(TraitTestBase):

    obj = AnyTrait()

    _default_value = None
    _good_values   = [10.0, 'ten', u'ten', [10], {'ten': 10},(10,), None, 1j]
    _bad_values    = []


class IntTrait(HasTraits):

    value = Int(99)

class TestInt(TraitTestBase):

    obj = IntTrait()
    _default_value = 99
    _good_values   = [10, -10]
    _bad_values    = ['ten', u'ten', [10], {'ten': 10},(10,), None, 1j,
                      10.1, -10.1, '10L', '-10L', '10.1', '-10.1', u'10L',
                      u'-10L', u'10.1', u'-10.1',  '10', '-10', u'10', u'-10']
    if not py3compat.PY3:
        _bad_values.extend([10L, -10L, 10*sys.maxint, -10*sys.maxint])


class LongTrait(HasTraits):

    value = Long(99L)

class TestLong(TraitTestBase):

    obj = LongTrait()

    _default_value = 99L
    _good_values   = [10, -10, 10L, -10L]
    _bad_values    = ['ten', u'ten', [10], [10l], {'ten': 10},(10,),(10L,),
                      None, 1j, 10.1, -10.1, '10', '-10', '10L', '-10L', '10.1',
                      '-10.1', u'10', u'-10', u'10L', u'-10L', u'10.1',
                      u'-10.1']
    if not py3compat.PY3:
        # maxint undefined on py3, because int == long
        _good_values.extend([10*sys.maxint, -10*sys.maxint])

    @skipif(py3compat.PY3, "not relevant on py3")
    def test_cast_small(self):
        """Long casts ints to long"""
        self.obj.value = 10
        self.assertEquals(type(self.obj.value), long)


class IntegerTrait(HasTraits):
    value = Integer(1)

class TestInteger(TestLong):
    obj = IntegerTrait()
    _default_value = 1

    def coerce(self, n):
        return int(n)

    @skipif(py3compat.PY3, "not relevant on py3")
    def test_cast_small(self):
        """Integer casts small longs to int"""
        if py3compat.PY3:
            raise SkipTest("not relevant on py3")

        self.obj.value = 100L
        self.assertEquals(type(self.obj.value), int)


class FloatTrait(HasTraits):

    value = Float(99.0)

class TestFloat(TraitTestBase):

    obj = FloatTrait()

    _default_value = 99.0
    _good_values   = [10, -10, 10.1, -10.1]
    _bad_values    = ['ten', u'ten', [10], {'ten': 10},(10,), None,
                      1j, '10', '-10', '10L', '-10L', '10.1', '-10.1', u'10',
                      u'-10', u'10L', u'-10L', u'10.1', u'-10.1']
    if not py3compat.PY3:
        _bad_values.extend([10L, -10L])


class ComplexTrait(HasTraits):

    value = Complex(99.0-99.0j)

class TestComplex(TraitTestBase):

    obj = ComplexTrait()

    _default_value = 99.0-99.0j
    _good_values   = [10, -10, 10.1, -10.1, 10j, 10+10j, 10-10j,
                      10.1j, 10.1+10.1j, 10.1-10.1j]
    _bad_values    = [u'10L', u'-10L', 'ten', [10], {'ten': 10},(10,), None]
    if not py3compat.PY3:
        _bad_values.extend([10L, -10L])


class BytesTrait(HasTraits):

    value = Bytes(b'string')

class TestBytes(TraitTestBase):

    obj = BytesTrait()

    _default_value = b'string'
    _good_values   = [b'10', b'-10', b'10L',
                      b'-10L', b'10.1', b'-10.1', b'string']
    _bad_values    = [10, -10, 10L, -10L, 10.1, -10.1, 1j, [10],
                      ['ten'],{'ten': 10},(10,), None,  u'string']


class UnicodeTrait(HasTraits):

    value = Unicode(u'unicode')

class TestUnicode(TraitTestBase):

    obj = UnicodeTrait()

    _default_value = u'unicode'
    _good_values   = ['10', '-10', '10L', '-10L', '10.1',
                      '-10.1', '', u'', 'string', u'string', u"€"]
    _bad_values    = [10, -10, 10L, -10L, 10.1, -10.1, 1j,
                      [10], ['ten'], [u'ten'], {'ten': 10},(10,), None]


class ObjectNameTrait(HasTraits):
    value = ObjectName("abc")

class TestObjectName(TraitTestBase):
    obj = ObjectNameTrait()

    _default_value = "abc"
    _good_values = ["a", "gh", "g9", "g_", "_G", u"a345_"]
    _bad_values = [1, "", u"€", "9g", "!", "#abc", "aj@", "a.b", "a()", "a[0]",
                                                            object(), object]
    if sys.version_info[0] < 3:
        _bad_values.append(u"þ")
    else:
        _good_values.append(u"þ")  # þ=1 is valid in Python 3 (PEP 3131).


class DottedObjectNameTrait(HasTraits):
    value = DottedObjectName("a.b")

class TestDottedObjectName(TraitTestBase):
    obj = DottedObjectNameTrait()

    _default_value = "a.b"
    _good_values = ["A", "y.t", "y765.__repr__", "os.path.join", u"os.path.join"]
    _bad_values = [1, u"abc.€", "_.@", ".", ".abc", "abc.", ".abc."]
    if sys.version_info[0] < 3:
        _bad_values.append(u"t.þ")
    else:
        _good_values.append(u"t.þ")


class TCPAddressTrait(HasTraits):

    value = TCPAddress()

class TestTCPAddress(TraitTestBase):

    obj = TCPAddressTrait()

    _default_value = ('127.0.0.1',0)
    _good_values = [('localhost',0),('192.168.0.1',1000),('www.google.com',80)]
    _bad_values = [(0,0),('localhost',10.0),('localhost',-1)]

class ListTrait(HasTraits):

    value = List(Int)

class TestList(TraitTestBase):

    obj = ListTrait()

    _default_value = []
    _good_values = [[], [1], range(10)]
    _bad_values = [10, [1,'a'], 'a', (1,2)]

class LenListTrait(HasTraits):

    value = List(Int, [0], minlen=1, maxlen=2)

class TestLenList(TraitTestBase):

    obj = LenListTrait()

    _default_value = [0]
    _good_values = [[1], range(2)]
    _bad_values = [10, [1,'a'], 'a', (1,2), [], range(3)]

class TupleTrait(HasTraits):

    value = Tuple(Int)

class TestTupleTrait(TraitTestBase):

    obj = TupleTrait()

    _default_value = None
    _good_values = [(1,), None,(0,)]
    _bad_values = [10, (1,2), [1],('a'), ()]

    def test_invalid_args(self):
        self.assertRaises(TypeError, Tuple, 5)
        self.assertRaises(TypeError, Tuple, default_value='hello')
        t = Tuple(Int, CBytes, default_value=(1,5))

class LooseTupleTrait(HasTraits):

    value = Tuple((1,2,3))

class TestLooseTupleTrait(TraitTestBase):

    obj = LooseTupleTrait()

    _default_value = (1,2,3)
    _good_values = [(1,), None, (0,), tuple(range(5)), tuple('hello'), ('a',5), ()]
    _bad_values = [10, 'hello', [1], []]

    def test_invalid_args(self):
        self.assertRaises(TypeError, Tuple, 5)
        self.assertRaises(TypeError, Tuple, default_value='hello')
        t = Tuple(Int, CBytes, default_value=(1,5))


class MultiTupleTrait(HasTraits):

    value = Tuple(Int, Bytes, default_value=[99,b'bottles'])

class TestMultiTuple(TraitTestBase):

    obj = MultiTupleTrait()

    _default_value = (99,b'bottles')
    _good_values = [(1,b'a'), (2,b'b')]
    _bad_values = ((),10, b'a', (1,b'a',3), (b'a',1), (1, u'a'))

class CRegExpTrait(HasTraits):

    value = CRegExp(r'')

class TestCRegExp(TraitTestBase):

    def coerce(self, value):
        return re.compile(value)

    obj = CRegExpTrait()

    _default_value = re.compile(r'')
    _good_values = [r'\d+', re.compile(r'\d+')]
    _bad_values = [r'(', None, ()]
