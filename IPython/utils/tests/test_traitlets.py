# encoding: utf-8
"""Tests for IPython.utils.traitlets."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
# 
# Adapted from enthought.traits, Copyright (c) Enthought, Inc.,
# also under the terms of the Modified BSD License.

import pickle
import re
import sys
from unittest import TestCase

import nose.tools as nt
from nose import SkipTest

from IPython.utils.traitlets import (
    HasTraits, MetaHasTraits, TraitType, Any, CBytes, Dict,
    Int, Long, Integer, Float, Complex, Bytes, Unicode, TraitError,
    Undefined, Type, This, Instance, TCPAddress, List, Tuple,
    ObjectName, DottedObjectName, CRegExp, link
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
        self.assertEqual(a.a, Undefined)

    def test_set(self):
        class A(HasTraitsStub):
            a = TraitType

        a = A()
        a.a = 10
        self.assertEqual(a.a, 10)
        self.assertEqual(a._notify_name, 'a')
        self.assertEqual(a._notify_old, Undefined)
        self.assertEqual(a._notify_new, 10)

    def test_validate(self):
        class MyTT(TraitType):
            def validate(self, inst, value):
                return -1
        class A(HasTraitsStub):
            tt = MyTT

        a = A()
        a.tt = 10
        self.assertEqual(a.tt, -1)

    def test_default_validate(self):
        class MyIntTT(TraitType):
            def validate(self, obj, value):
                if isinstance(value, int):
                    return value
                self.error(obj, value)
        class A(HasTraits):
            tt = MyIntTT(10)
        a = A()
        self.assertEqual(a.tt, 10)

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
        self.assertEqual(a.tt, 10)

    def test_value_for(self):
        class MyTT(TraitType):
            def value_for(self, value):
                return 20
        class A(HasTraits):
            tt = MyTT

        a = A()
        a.tt = 10
        self.assertEqual(a.tt, 20)

    def test_info(self):
        class A(HasTraits):
            tt = TraitType
        a = A()
        self.assertEqual(A.tt.info(), 'any value')

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
        self.assertEqual(a._trait_values, {})
        self.assertEqual(list(a._trait_dyn_inits.keys()), ['x'])
        self.assertEqual(a.x, 11)
        self.assertEqual(a._trait_values, {'x': 11})
        b = B()
        self.assertEqual(b._trait_values, {'x': 20})
        self.assertEqual(list(a._trait_dyn_inits.keys()), ['x'])
        self.assertEqual(b.x, 20)
        c = C()
        self.assertEqual(c._trait_values, {})
        self.assertEqual(list(a._trait_dyn_inits.keys()), ['x'])
        self.assertEqual(c.x, 21)
        self.assertEqual(c._trait_values, {'x': 21})
        # Ensure that the base class remains unmolested when the _default
        # initializer gets overridden in a subclass.
        a = A()
        c = C()
        self.assertEqual(a._trait_values, {})
        self.assertEqual(list(a._trait_dyn_inits.keys()), ['x'])
        self.assertEqual(a.x, 11)
        self.assertEqual(a._trait_values, {'x': 11})



class TestHasTraitsMeta(TestCase):

    def test_metaclass(self):
        self.assertEqual(type(HasTraits), MetaHasTraits)

        class A(HasTraits):
            a = Int

        a = A()
        self.assertEqual(type(a.__class__), MetaHasTraits)
        self.assertEqual(a.a,0)
        a.a = 10
        self.assertEqual(a.a,10)

        class B(HasTraits):
            b = Int()

        b = B()
        self.assertEqual(b.b,0)
        b.b = 10
        self.assertEqual(b.b,10)

        class C(HasTraits):
            c = Int(30)

        c = C()
        self.assertEqual(c.c,30)
        c.c = 10
        self.assertEqual(c.c,10)

    def test_this_class(self):
        class A(HasTraits):
            t = This()
            tt = This()
        class B(A):
            tt = This()
            ttt = This()
        self.assertEqual(A.t.this_class, A)
        self.assertEqual(B.t.this_class, A)
        self.assertEqual(B.tt.this_class, B)
        self.assertEqual(B.ttt.this_class, B)

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
        self.assertEqual(len(self._notify1),0)
        a.b = 0.0
        self.assertEqual(len(self._notify1),0)
        a.a = 10
        self.assertTrue(('a',0,10) in self._notify1)
        a.b = 10.0
        self.assertTrue(('b',0.0,10.0) in self._notify1)
        self.assertRaises(TraitError,setattr,a,'a','bad string')
        self.assertRaises(TraitError,setattr,a,'b','bad string')
        self._notify1 = []
        a.on_trait_change(self.notify1,remove=True)
        a.a = 20
        a.b = 20.0
        self.assertEqual(len(self._notify1),0)

    def test_notify_one(self):

        class A(HasTraits):
            a = Int
            b = Float

        a = A()
        a.on_trait_change(self.notify1, 'a')
        a.a = 0
        self.assertEqual(len(self._notify1),0)
        a.a = 10
        self.assertTrue(('a',0,10) in self._notify1)
        self.assertRaises(TraitError,setattr,a,'a','bad string')

    def test_subclass(self):

        class A(HasTraits):
            a = Int

        class B(A):
            b = Float

        b = B()
        self.assertEqual(b.a,0)
        self.assertEqual(b.b,0.0)
        b.a = 100
        b.b = 100.0
        self.assertEqual(b.a,100)
        self.assertEqual(b.b,100.0)

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
        self.assertEqual(len(self._notify1),0)
        self.assertEqual(len(self._notify2),0)
        b.a = 10
        b.b = 10.0
        self.assertTrue(('a',0,10) in self._notify1)
        self.assertTrue(('b',0.0,10.0) in self._notify2)

    def test_static_notify(self):

        class A(HasTraits):
            a = Int
            _notify1 = []
            def _a_changed(self, name, old, new):
                self._notify1.append((name, old, new))

        a = A()
        a.a = 0
        # This is broken!!!
        self.assertEqual(len(a._notify1),0)
        a.a = 10
        self.assertTrue(('a',0,10) in a._notify1)

        class B(A):
            b = Float
            _notify2 = []
            def _b_changed(self, name, old, new):
                self._notify2.append((name, old, new))

        b = B()
        b.a = 10
        b.b = 10.0
        self.assertTrue(('a',0,10) in b._notify1)
        self.assertTrue(('b',0.0,10.0) in b._notify2)

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
        self.assertEqual(self.cb,())
        a.on_trait_change(callback0, 'a', remove=True)

        a.on_trait_change(callback1, 'a')
        a.a = 100
        self.assertEqual(self.cb,('a',))
        a.on_trait_change(callback1, 'a', remove=True)

        a.on_trait_change(callback2, 'a')
        a.a = 1000
        self.assertEqual(self.cb,('a',1000))
        a.on_trait_change(callback2, 'a', remove=True)

        a.on_trait_change(callback3, 'a')
        a.a = 10000
        self.assertEqual(self.cb,('a',1000,10000))
        a.on_trait_change(callback3, 'a', remove=True)

        self.assertEqual(len(a._trait_notifiers['a']),0)

    def test_notify_only_once(self):

        class A(HasTraits):
            listen_to = ['a']
            
            a = Int(0)
            b = 0
            
            def __init__(self, **kwargs):
                super(A, self).__init__(**kwargs)
                self.on_trait_change(self.listener1, ['a'])
            
            def listener1(self, name, old, new):
                self.b += 1

        class B(A):
                    
            c = 0
            d = 0
            
            def __init__(self, **kwargs):
                super(B, self).__init__(**kwargs)
                self.on_trait_change(self.listener2)
            
            def listener2(self, name, old, new):
                self.c += 1
            
            def _a_changed(self, name, old, new):
                self.d += 1

        b = B()
        b.a += 1
        self.assertEqual(b.b, b.c)
        self.assertEqual(b.b, b.d)
        b.a += 1
        self.assertEqual(b.b, b.c)
        self.assertEqual(b.b, b.d)


class TestHasTraits(TestCase):

    def test_trait_names(self):
        class A(HasTraits):
            i = Int
            f = Float
        a = A()
        self.assertEqual(sorted(a.trait_names()),['f','i'])
        self.assertEqual(sorted(A.class_trait_names()),['f','i'])

    def test_trait_metadata(self):
        class A(HasTraits):
            i = Int(config_key='MY_VALUE')
        a = A()
        self.assertEqual(a.trait_metadata('i','config_key'), 'MY_VALUE')

    def test_traits(self):
        class A(HasTraits):
            i = Int
            f = Float
        a = A()
        self.assertEqual(a.traits(), dict(i=A.i, f=A.f))
        self.assertEqual(A.class_traits(), dict(i=A.i, f=A.f))

    def test_traits_metadata(self):
        class A(HasTraits):
            i = Int(config_key='VALUE1', other_thing='VALUE2')
            f = Float(config_key='VALUE3', other_thing='VALUE2')
            j = Int(0)
        a = A()
        self.assertEqual(a.traits(), dict(i=A.i, f=A.f, j=A.j))
        traits = a.traits(config_key='VALUE1', other_thing='VALUE2')
        self.assertEqual(traits, dict(i=A.i))

        # This passes, but it shouldn't because I am replicating a bug in
        # traits.
        traits = a.traits(config_key=lambda v: True)
        self.assertEqual(traits, dict(i=A.i, f=A.f, j=A.j))

    def test_init(self):
        class A(HasTraits):
            i = Int()
            x = Float()
        a = A(i=1, x=10.0)
        self.assertEqual(a.i, 1)
        self.assertEqual(a.x, 10.0)

    def test_positional_args(self):
        class A(HasTraits):
            i = Int(0)
            def __init__(self, i):
                super(A, self).__init__()
                self.i = i
        
        a = A(5)
        self.assertEqual(a.i, 5)
        # should raise TypeError if no positional arg given
        self.assertRaises(TypeError, A)

#-----------------------------------------------------------------------------
# Tests for specific trait types
#-----------------------------------------------------------------------------


class TestType(TestCase):

    def test_default(self):

        class B(object): pass
        class A(HasTraits):
            klass = Type

        a = A()
        self.assertEqual(a.klass, None)

        a.klass = B
        self.assertEqual(a.klass, B)
        self.assertRaises(TraitError, setattr, a, 'klass', 10)

    def test_value(self):

        class B(object): pass
        class C(object): pass
        class A(HasTraits):
            klass = Type(B)

        a = A()
        self.assertEqual(a.klass, B)
        self.assertRaises(TraitError, setattr, a, 'klass', C)
        self.assertRaises(TraitError, setattr, a, 'klass', object)
        a.klass = B

    def test_allow_none(self):

        class B(object): pass
        class C(B): pass
        class A(HasTraits):
            klass = Type(B, allow_none=False)

        a = A()
        self.assertEqual(a.klass, B)
        self.assertRaises(TraitError, setattr, a, 'klass', None)
        a.klass = C
        self.assertEqual(a.klass, C)

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
        self.assertEqual(a.klass, Struct)

        self.assertRaises(TraitError, setattr, a, 'klass', 10)

    def test_set_str_klass(self):

        class A(HasTraits):
            klass = Type()

        a = A(klass='IPython.utils.ipstruct.Struct')
        from IPython.utils.ipstruct import Struct
        self.assertEqual(a.klass, Struct)

class TestInstance(TestCase):

    def test_basic(self):
        class Foo(object): pass
        class Bar(Foo): pass
        class Bah(object): pass

        class A(HasTraits):
            inst = Instance(Foo)

        a = A()
        self.assertTrue(a.inst is None)
        a.inst = Foo()
        self.assertTrue(isinstance(a.inst, Foo))
        a.inst = Bar()
        self.assertTrue(isinstance(a.inst, Foo))
        self.assertRaises(TraitError, setattr, a, 'inst', Foo)
        self.assertRaises(TraitError, setattr, a, 'inst', Bar)
        self.assertRaises(TraitError, setattr, a, 'inst', Bah())

    def test_default_klass(self):
        class Foo(object): pass
        class Bar(Foo): pass
        class Bah(object): pass

        class FooInstance(Instance):
            klass = Foo

        class A(HasTraits):
            inst = FooInstance()

        a = A()
        self.assertTrue(a.inst is None)
        a.inst = Foo()
        self.assertTrue(isinstance(a.inst, Foo))
        a.inst = Bar()
        self.assertTrue(isinstance(a.inst, Foo))
        self.assertRaises(TraitError, setattr, a, 'inst', Foo)
        self.assertRaises(TraitError, setattr, a, 'inst', Bar)
        self.assertRaises(TraitError, setattr, a, 'inst', Bah())

    def test_unique_default_value(self):
        class Foo(object): pass
        class A(HasTraits):
            inst = Instance(Foo,(),{})

        a = A()
        b = A()
        self.assertTrue(a.inst is not b.inst)

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
        self.assertEqual(a.inst.c, 10)

        class B(HasTraits):
            inst = Instance(Bah, args=(10,), kw=dict(d=20))
        b = B()
        self.assertEqual(b.inst.c, 10)
        self.assertEqual(b.inst.d, 20)

        class C(HasTraits):
            inst = Instance(Foo)
        c = C()
        self.assertTrue(c.inst is None)

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
        self.assertEqual(f.this, None)
        g = Foo()
        f.this = g
        self.assertEqual(f.this, g)
        self.assertRaises(TraitError, setattr, f, 'this', 10)

    def test_this_inst(self):
        class Foo(HasTraits):
            this = This()

        f = Foo()
        f.this = Foo()
        self.assertTrue(isinstance(f.this, Foo))

    def test_subclass(self):
        class Foo(HasTraits):
            t = This()
        class Bar(Foo):
            pass
        f = Foo()
        b = Bar()
        f.t = b
        b.t = f
        self.assertEqual(f.t, b)
        self.assertEqual(b.t, f)

    def test_subclass_override(self):
        class Foo(HasTraits):
            t = This()
        class Bar(Foo):
            t = This()
        f = Foo()
        b = Bar()
        f.t = b
        self.assertEqual(f.t, b)
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
                self.assertEqual(self.obj.value, self.coerce(value))

    def test_bad_values(self):
        if hasattr(self, '_bad_values'):
            for value in self._bad_values:
                try:
                    self.assertRaises(TraitError, self.assign, value)
                except AssertionError:
                    assert False, value

    def test_default_value(self):
        if hasattr(self, '_default_value'):
            self.assertEqual(self._default_value, self.obj.value)

    def test_allow_none(self):
        if (hasattr(self, '_bad_values') and hasattr(self, '_good_values') and
        None in self._bad_values):
            trait=self.obj.traits()['value']
            try:
                trait.allow_none = True
                self._bad_values.remove(None)
                #skip coerce. Allow None casts None to None.
                self.assign(None)
                self.assertEqual(self.obj.value,None)
                self.test_good_values()
                self.test_bad_values()
            finally:
                #tear down
                trait.allow_none = False
                self._bad_values.append(None)

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
        _bad_values.extend([long(10), long(-10), 10*sys.maxint, -10*sys.maxint])


class LongTrait(HasTraits):

    value = Long(99 if py3compat.PY3 else long(99))

class TestLong(TraitTestBase):

    obj = LongTrait()

    _default_value = 99 if py3compat.PY3 else long(99)
    _good_values   = [10, -10]
    _bad_values    = ['ten', u'ten', [10], {'ten': 10},(10,),
                      None, 1j, 10.1, -10.1, '10', '-10', '10L', '-10L', '10.1',
                      '-10.1', u'10', u'-10', u'10L', u'-10L', u'10.1',
                      u'-10.1']
    if not py3compat.PY3:
        # maxint undefined on py3, because int == long
        _good_values.extend([long(10), long(-10), 10*sys.maxint, -10*sys.maxint])
        _bad_values.extend([[long(10)], (long(10),)])

    @skipif(py3compat.PY3, "not relevant on py3")
    def test_cast_small(self):
        """Long casts ints to long"""
        self.obj.value = 10
        self.assertEqual(type(self.obj.value), long)


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

        self.obj.value = long(100)
        self.assertEqual(type(self.obj.value), int)


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
        _bad_values.extend([long(10), long(-10)])


class ComplexTrait(HasTraits):

    value = Complex(99.0-99.0j)

class TestComplex(TraitTestBase):

    obj = ComplexTrait()

    _default_value = 99.0-99.0j
    _good_values   = [10, -10, 10.1, -10.1, 10j, 10+10j, 10-10j,
                      10.1j, 10.1+10.1j, 10.1-10.1j]
    _bad_values    = [u'10L', u'-10L', 'ten', [10], {'ten': 10},(10,), None]
    if not py3compat.PY3:
        _bad_values.extend([long(10), long(-10)])


class BytesTrait(HasTraits):

    value = Bytes(b'string')

class TestBytes(TraitTestBase):

    obj = BytesTrait()

    _default_value = b'string'
    _good_values   = [b'10', b'-10', b'10L',
                      b'-10L', b'10.1', b'-10.1', b'string']
    _bad_values    = [10, -10, 10.1, -10.1, 1j, [10],
                      ['ten'],{'ten': 10},(10,), None,  u'string']
    if not py3compat.PY3:
        _bad_values.extend([long(10), long(-10)])


class UnicodeTrait(HasTraits):

    value = Unicode(u'unicode')

class TestUnicode(TraitTestBase):

    obj = UnicodeTrait()

    _default_value = u'unicode'
    _good_values   = ['10', '-10', '10L', '-10L', '10.1',
                      '-10.1', '', u'', 'string', u'string', u"€"]
    _bad_values    = [10, -10, 10.1, -10.1, 1j,
                      [10], ['ten'], [u'ten'], {'ten': 10},(10,), None]
    if not py3compat.PY3:
        _bad_values.extend([long(10), long(-10)])


class ObjectNameTrait(HasTraits):
    value = ObjectName("abc")

class TestObjectName(TraitTestBase):
    obj = ObjectNameTrait()

    _default_value = "abc"
    _good_values = ["a", "gh", "g9", "g_", "_G", u"a345_"]
    _bad_values = [1, "", u"€", "9g", "!", "#abc", "aj@", "a.b", "a()", "a[0]",
                                                        None, object(), object]
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
    _bad_values = [1, u"abc.€", "_.@", ".", ".abc", "abc.", ".abc.", None]
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
    _bad_values = [(0,0),('localhost',10.0),('localhost',-1), None]

class ListTrait(HasTraits):

    value = List(Int)

class TestList(TraitTestBase):

    obj = ListTrait()

    _default_value = []
    _good_values = [[], [1], list(range(10)), (1,2)]
    _bad_values = [10, [1,'a'], 'a']
    
    def coerce(self, value):
        if value is not None:
            value = list(value)
        return value

class Foo(object):
    pass

class InstanceListTrait(HasTraits):

    value = List(Instance(__name__+'.Foo'))

class TestInstanceList(TraitTestBase):

    obj = InstanceListTrait()

    def test_klass(self):
        """Test that the instance klass is properly assigned."""
        self.assertIs(self.obj.traits()['value']._trait.klass, Foo)

    _default_value = []
    _good_values = [[Foo(), Foo(), None], None]
    _bad_values = [['1', 2,], '1', [Foo]]

class LenListTrait(HasTraits):

    value = List(Int, [0], minlen=1, maxlen=2)

class TestLenList(TraitTestBase):

    obj = LenListTrait()

    _default_value = [0]
    _good_values = [[1], [1,2], (1,2)]
    _bad_values = [10, [1,'a'], 'a', [], list(range(3))]

    def coerce(self, value):
        if value is not None:
            value = list(value)
        return value

class TupleTrait(HasTraits):

    value = Tuple(Int(allow_none=True))

class TestTupleTrait(TraitTestBase):

    obj = TupleTrait()

    _default_value = None
    _good_values = [(1,), None, (0,), [1], (None,)]
    _bad_values = [10, (1,2), ('a'), ()]

    def coerce(self, value):
        if value is not None:
            value = tuple(value)
        return value

    def test_invalid_args(self):
        self.assertRaises(TypeError, Tuple, 5)
        self.assertRaises(TypeError, Tuple, default_value='hello')
        t = Tuple(Int, CBytes, default_value=(1,5))

class LooseTupleTrait(HasTraits):

    value = Tuple((1,2,3))

class TestLooseTupleTrait(TraitTestBase):

    obj = LooseTupleTrait()

    _default_value = (1,2,3)
    _good_values = [(1,), None, [1], (0,), tuple(range(5)), tuple('hello'), ('a',5), ()]
    _bad_values = [10, 'hello', {}]

    def coerce(self, value):
        if value is not None:
            value = tuple(value)
        return value

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

class DictTrait(HasTraits):
    value = Dict()

def test_dict_assignment():
    d = dict()
    c = DictTrait()
    c.value = d
    d['a'] = 5
    nt.assert_equal(d, c.value)
    nt.assert_true(c.value is d)

class TestLink(TestCase):
    def test_connect_same(self):
        """Verify two traitlets of the same type can be linked together using link."""

        # Create two simple classes with Int traitlets.
        class A(HasTraits):
            value = Int()
        a = A(value=9)
        b = A(value=8)

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'value'))

        # Make sure the values are the same at the point of linking.
        self.assertEqual(a.value, b.value)

        # Change one of the values to make sure they stay in sync.
        a.value = 5
        self.assertEqual(a.value, b.value)
        b.value = 6
        self.assertEqual(a.value, b.value)

    def test_link_different(self):
        """Verify two traitlets of different types can be linked together using link."""

        # Create two simple classes with Int traitlets.
        class A(HasTraits):
            value = Int()
        class B(HasTraits):
            count = Int()
        a = A(value=9)
        b = B(count=8)

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'count'))

        # Make sure the values are the same at the point of linking.
        self.assertEqual(a.value, b.count)

        # Change one of the values to make sure they stay in sync.
        a.value = 5
        self.assertEqual(a.value, b.count)
        b.count = 4
        self.assertEqual(a.value, b.count)

    def test_unlink(self):
        """Verify two linked traitlets can be unlinked."""

        # Create two simple classes with Int traitlets.
        class A(HasTraits):
            value = Int()
        a = A(value=9)
        b = A(value=8)

        # Connect the two classes.
        c = link((a, 'value'), (b, 'value'))
        a.value = 4
        c.unlink()

        # Change one of the values to make sure they don't stay in sync.
        a.value = 5
        self.assertNotEqual(a.value, b.value)

    def test_callbacks(self):
        """Verify two linked traitlets have their callbacks called once."""

        # Create two simple classes with Int traitlets.
        class A(HasTraits):
            value = Int()
        class B(HasTraits):
            count = Int()
        a = A(value=9)
        b = B(count=8)
        
        # Register callbacks that count.
        callback_count = []
        def a_callback(name, old, new):
            callback_count.append('a')
        a.on_trait_change(a_callback, 'value')
        def b_callback(name, old, new):
            callback_count.append('b')
        b.on_trait_change(b_callback, 'count')

        # Connect the two classes.
        c = link((a, 'value'), (b, 'count'))

        # Make sure b's count was set to a's value once.
        self.assertEqual(''.join(callback_count), 'b')
        del callback_count[:]

        # Make sure a's value was set to b's count once.
        b.count = 5
        self.assertEqual(''.join(callback_count), 'ba')
        del callback_count[:]

        # Make sure b's count was set to a's value once.
        a.value = 4
        self.assertEqual(''.join(callback_count), 'ab')
        del callback_count[:]

class Pickleable(HasTraits):
    i = Int()
    j = Int()
    
    def _i_default(self):
        return 1
    
    def _i_changed(self, name, old, new):
        self.j = new

def test_pickle_hastraits():
    c = Pickleable()
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        p = pickle.dumps(c, protocol)
        c2 = pickle.loads(p)
        nt.assert_equal(c2.i, c.i)
        nt.assert_equal(c2.j, c.j)

    c.i = 5
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        p = pickle.dumps(c, protocol)
        c2 = pickle.loads(p)
        nt.assert_equal(c2.i, c.i)
        nt.assert_equal(c2.j, c.j)
    
