#!/usr/bin/env python
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
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import os


from unittest import TestCase

from IPython.utils.traitlets import (
    HasTraitlets, MetaHasTraitlets, TraitletType, Any,
    Int, Long, Float, Complex, Str, Unicode, Bool, TraitletError,
    Undefined, Type, Instance, This
)


#-----------------------------------------------------------------------------
# Helper classes for testing
#-----------------------------------------------------------------------------


class HasTraitletsStub(object):

    def __init__(self):
        self._traitlet_values = {}
        self._traitlet_notifiers = {}

    def _notify_traitlet(self, name, old, new):
        self._notify_name = name
        self._notify_old = old
        self._notify_new = new


#-----------------------------------------------------------------------------
# Test classes
#-----------------------------------------------------------------------------


class TestTraitletType(TestCase):

    name = 'a'

    def setUp(self):
        self.tt = TraitletType()
        self.tt.name = self.name
        self.hast = HasTraitletsStub() 

    def test_get_undefined(self):
        value = self.tt.__get__(self.hast)
        self.assertEquals(value, Undefined)

    def test_set(self):
        self.tt.__set__(self.hast, 10)
        self.assertEquals(self.hast._traitlet_values[self.name],10)
        self.assertEquals(self.hast._notify_name,self.name)
        self.assertEquals(self.hast._notify_old,Undefined)
        self.assertEquals(self.hast._notify_new,10)

    def test_validate(self):
        class MyTT(TraitletType):
            def validate(self, inst, value):
                return -1
        tt = MyTT()
        tt.name = self.name
        tt.__set__(self.hast, 10)
        self.assertEquals(tt.__get__(self.hast),-1)

    def test_default_validate(self):
        class MyIntTT(TraitletType):
            def validate(self, obj, value):
                if isinstance(value, int):
                    return value
                self.error(obj, value)
        tt = MyIntTT(10)
        tt.name = 'a'
        self.assertEquals(tt.__get__(self.hast), 10)
        tt = MyIntTT('bad default')
        tt.name = 'b' # different name from 'a' as we want an unset dv
        self.assertRaises(TraitletError, tt.__get__, self.hast)
            

    def test_is_valid_for(self):
        class MyTT(TraitletType):
            def is_valid_for(self, value):
                return True
        tt = MyTT()
        tt.name = self.name
        tt.__set__(self.hast, 10)
        self.assertEquals(tt.__get__(self.hast), 10)

    def test_value_for(self):
        class MyTT(TraitletType):
            def value_for(self, value):
                return 20
        tt = MyTT()
        tt.name = self.name
        tt.__set__(self.hast, 10)
        self.assertEquals(tt.__get__(self.hast), 20)

    def test_info(self):
        self.assertEquals(self.tt.info(), 'any value')

    def test_error(self):
        self.assertRaises(TraitletError, self.tt.error, self.hast, 10)


class TestHasTraitletsMeta(TestCase):

    def test_metaclass(self):
        self.assertEquals(type(HasTraitlets), MetaHasTraitlets)

        class A(HasTraitlets):
            a = Int

        a = A()
        self.assertEquals(type(a.__class__), MetaHasTraitlets)
        self.assertEquals(a.a,0)
        a.a = 10
        self.assertEquals(a.a,10)

        class B(HasTraitlets):
            b = Int()

        b = B()
        self.assertEquals(b.b,0)
        b.b = 10
        self.assertEquals(b.b,10)

        class C(HasTraitlets):
            c = Int(30)

        c = C()
        self.assertEquals(c.c,30)
        c.c = 10
        self.assertEquals(c.c,10)


class TestHasTraitletsNotify(TestCase):

    def setUp(self):
        self._notify1 = []
        self._notify2 = []

    def notify1(self, name, old, new):
        self._notify1.append((name, old, new))

    def notify2(self, name, old, new):
        self._notify2.append((name, old, new))

    def test_notify_all(self):

        class A(HasTraitlets):
            a = Int
            b = Float

        a = A()
        a.on_traitlet_change(self.notify1)
        a.a = 0
        self.assertEquals(len(self._notify1),0)
        a.b = 0.0
        self.assertEquals(len(self._notify1),0)
        a.a = 10
        self.assert_(('a',0,10) in self._notify1)
        a.b = 10.0
        self.assert_(('b',0.0,10.0) in self._notify1)
        self.assertRaises(TraitletError,setattr,a,'a','bad string')
        self.assertRaises(TraitletError,setattr,a,'b','bad string')
        self._notify1 = []
        a.on_traitlet_change(self.notify1,remove=True)
        a.a = 20
        a.b = 20.0
        self.assertEquals(len(self._notify1),0)

    def test_notify_one(self):

        class A(HasTraitlets):
            a = Int
            b = Float

        a = A()
        a.on_traitlet_change(self.notify1, 'a')
        a.a = 0
        self.assertEquals(len(self._notify1),0)
        a.a = 10
        self.assert_(('a',0,10) in self._notify1)
        self.assertRaises(TraitletError,setattr,a,'a','bad string')

    def test_subclass(self):

        class A(HasTraitlets):
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

        class A(HasTraitlets):
            a = Int

        class B(A):
            b = Float

        b = B()
        b.on_traitlet_change(self.notify1, 'a')
        b.on_traitlet_change(self.notify2, 'b')
        b.a = 0
        b.b = 0.0
        self.assertEquals(len(self._notify1),0)
        self.assertEquals(len(self._notify2),0)
        b.a = 10
        b.b = 10.0
        self.assert_(('a',0,10) in self._notify1)
        self.assert_(('b',0.0,10.0) in self._notify2)

    def test_static_notify(self):

        class A(HasTraitlets):
            a = Int
            _notify1 = []
            def _a_changed(self, name, old, new):
                self._notify1.append((name, old, new))

        a = A()
        a.a = 0
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

        class A(HasTraitlets):
            a = Int

        a = A()
        a.on_traitlet_change(callback0, 'a')
        a.a = 10
        self.assertEquals(self.cb,())
        a.on_traitlet_change(callback0, 'a', remove=True)

        a.on_traitlet_change(callback1, 'a')
        a.a = 100
        self.assertEquals(self.cb,('a',))
        a.on_traitlet_change(callback1, 'a', remove=True)

        a.on_traitlet_change(callback2, 'a')
        a.a = 1000
        self.assertEquals(self.cb,('a',1000))
        a.on_traitlet_change(callback2, 'a', remove=True)

        a.on_traitlet_change(callback3, 'a')
        a.a = 10000
        self.assertEquals(self.cb,('a',1000,10000))
        a.on_traitlet_change(callback3, 'a', remove=True)

        self.assertEquals(len(a._traitlet_notifiers['a']),0)


class TestAddTraitlet(TestCase):

    def test_add_float(self):

        class A(HasTraitlets):
            a = Int
        
        a = A()
        a.a = 10
        a._add_class_traitlet('b',Float)
        self.assertEquals(a.b,0.0)
        a.b = 10.0
        self.assertEquals(a.b,10.0)
        self.assertRaises(TraitletError, setattr, a, 'b', 'bad value')

class TestTraitletKeys(TestCase):

    def test_keys(self):
        class A(HasTraitlets):
            a = Int
            b = Float
        a = A()
        self.assertEquals(a.traitlet_keys(),['a','b'])


#-----------------------------------------------------------------------------
# Tests for specific traitlet types
#-----------------------------------------------------------------------------


class TestType(TestCase):

    def test_default(self):

        class B(object): pass
        class A(HasTraitlets):
            klass = Type

        a = A()
        self.assertEquals(a.klass, None)
        a.klass = B
        self.assertEquals(a.klass, B)
        self.assertRaises(TraitletError, setattr, a, 'klass', 10)

    def test_value(self):

        class B(object): pass
        class C(object): pass
        class A(HasTraitlets):
            klass = Type(B)
        
        a = A()
        self.assertEquals(a.klass, B)
        self.assertRaises(TraitletError, setattr, a, 'klass', C)
        self.assertRaises(TraitletError, setattr, a, 'klass', object)
        a.klass = B

    def test_allow_none(self):

        class B(object): pass
        class C(B): pass
        class A(HasTraitlets):
            klass = Type(B, allow_none=False)

        a = A()
        self.assertEquals(a.klass, B)
        self.assertRaises(TraitletError, setattr, a, 'klass', None)
        a.klass = C
        self.assertEquals(a.klass, C)


class TestInstance(TestCase):

    def test_basic(self):
        class Foo(object): pass
        class Bar(Foo): pass
        class Bah(object): pass
        
        class A(HasTraitlets):
            inst = Instance(Foo)

        a = A()
        self.assert_(isinstance(a.inst, Foo))
        a.inst = Foo()
        self.assert_(isinstance(a.inst, Foo))
        a.inst = Bar()
        self.assert_(isinstance(a.inst, Foo))
        self.assertRaises(TraitletError, setattr, a, 'inst', Foo)
        self.assertRaises(TraitletError, setattr, a, 'inst', Bar)
        self.assertRaises(TraitletError, setattr, a, 'inst', Bah())

    def test_unique_default_value(self):
        class Foo(object): pass        
        class A(HasTraitlets):
            inst = Instance(Foo)

        a = A()
        b = A()
        self.assert_(a.inst is not b.inst)

    def test_args_kw(self):
        class Foo(object):
            def __init__(self, c): self.c = c

        class A(HasTraitlets):
            inst = Instance(Foo, args=(10,))

        a = A()
        self.assertEquals(a.inst.c, 10)

        class Bar(object):
            def __init__(self, c, d):
                self.c = c; self.d = d

        class B(HasTraitlets):
            inst = Instance(Bar, args=(10,),kw=dict(d=20))
        b = B()
        self.assertEquals(b.inst.c, 10)
        self.assertEquals(b.inst.d, 20)

    def test_instance(self):
        # Does passing an instance yield a default value of None?
        class Foo(object): pass

        class A(HasTraitlets):
            inst = Instance(Foo())
        a = A()
        self.assertEquals(a.inst, None)
        
        class B(HasTraitlets):
            inst = Instance(Foo(), allow_none=False)
        b = B()
        self.assertRaises(TraitletError, getattr, b, 'inst')


class TestThis(TestCase):

    def test_this_class(self):
        class Foo(HasTraitlets):
            this = This

        f = Foo()
        self.assertEquals(f.this, None)
        g = Foo()
        f.this = g
        self.assertEquals(f.this, g)
        self.assertRaises(TraitletError, setattr, f, 'this', 10)

    def test_this_inst(self):
        class Foo(HasTraitlets):
            this = This()
        
        f = Foo()
        f.this = Foo()
        self.assert_(isinstance(f.this, Foo))

    def test_allow_none(self):
        class Foo(HasTraitlets):
            this = This(allow_none=False)

        f = Foo()
        g = Foo()
        f.this = g
        self.assertEquals(f.this, g)

        f = Foo()
        self.assertRaises(TraitletError, getattr, f, 'this')

        f = Foo()
        self.assertRaises(TraitletError, setattr, f, 'this', None)


class TraitletTestBase(TestCase):
    """A best testing class for basic traitlet types."""

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
                self.assertRaises(TraitletError, self.assign, value)

    def test_default_value(self):
        if hasattr(self, '_default_value'):
            self.assertEquals(self._default_value, self.obj.value)


class AnyTraitlet(HasTraitlets):

    value = Any

class AnyTraitTest(TraitletTestBase):

    obj = AnyTraitlet()

    _default_value = None
    _good_values   = [10.0, 'ten', u'ten', [10], {'ten': 10},(10,), None, 1j]
    _bad_values    = []


class IntTraitlet(HasTraitlets):

    value = Int(99)

class TestInt(TraitletTestBase):

    obj = IntTraitlet()
    _default_value = 99
    _good_values   = [10, -10]
    _bad_values    = ['ten', u'ten', [10], {'ten': 10},(10,), None, 1j, 10L,
                      -10L, 10.1, -10.1, '10L', '-10L', '10.1', '-10.1', u'10L',
                      u'-10L', u'10.1', u'-10.1',  '10', '-10', u'10', u'-10']


class LongTraitlet(HasTraitlets):

    value = Long(99L)

class TestLong(TraitletTestBase):

    obj = LongTraitlet()

    _default_value = 99L
    _good_values   = [10, -10, 10L, -10L]
    _bad_values    = ['ten', u'ten', [10], [10l], {'ten': 10},(10,),(10L,),
                      None, 1j, 10.1, -10.1, '10', '-10', '10L', '-10L', '10.1',
                      '-10.1', u'10', u'-10', u'10L', u'-10L', u'10.1',
                      u'-10.1']


class FloatTraitlet(HasTraitlets):

    value = Float(99.0)

class TestFloat(TraitletTestBase):

    obj = FloatTraitlet()

    _default_value = 99.0
    _good_values   = [10, -10, 10.1, -10.1]
    _bad_values    = [10L, -10L, 'ten', u'ten', [10], {'ten': 10},(10,), None,
                      1j, '10', '-10', '10L', '-10L', '10.1', '-10.1', u'10',
                      u'-10', u'10L', u'-10L', u'10.1', u'-10.1']


class ComplexTraitlet(HasTraitlets):

    value = Complex(99.0-99.0j)

class TestComplex(TraitletTestBase):

    obj = ComplexTraitlet()

    _default_value = 99.0-99.0j
    _good_values   = [10, -10, 10.1, -10.1, 10j, 10+10j, 10-10j, 
                      10.1j, 10.1+10.1j, 10.1-10.1j]
    _bad_values    = [10L, -10L, u'10L', u'-10L', 'ten', [10], {'ten': 10},(10,), None]


class StringTraitlet(HasTraitlets):

    value = Str('string')

class TestString(TraitletTestBase):

    obj = StringTraitlet()

    _default_value = 'string'
    _good_values   = ['10', '-10', '10L',
                      '-10L', '10.1', '-10.1', 'string']
    _bad_values    = [10, -10, 10L, -10L, 10.1, -10.1, 1j, [10],
                      ['ten'],{'ten': 10},(10,), None,  u'string']


class UnicodeTraitlet(HasTraitlets):

    value = Unicode(u'unicode')

class TestUnicode(TraitletTestBase):

    obj = UnicodeTraitlet()

    _default_value = u'unicode'
    _good_values   = ['10', '-10', '10L', '-10L', '10.1', 
                      '-10.1', '', u'', 'string', u'string', ]
    _bad_values    = [10, -10, 10L, -10L, 10.1, -10.1, 1j,
                      [10], ['ten'], [u'ten'], {'ten': 10},(10,), None]
