#!/usr/bin/env python
# encoding: utf-8
"""
Tests for IPython.core.component

Authors:

* Brian Granger
* Fernando Perez (design help)
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

from unittest import TestCase

from IPython.core.component import Component, ComponentError
from IPython.utils.traitlets import (
    TraitletError, Int, Float, Str
)
from IPython.config.loader import Config


#-----------------------------------------------------------------------------
# Test cases
#-----------------------------------------------------------------------------


class TestComponentMeta(TestCase):

    def test_get_instances(self):
        class BaseComponent(Component):
            pass
        c1 = BaseComponent(None)
        c2 = BaseComponent(c1)
        self.assertEquals(BaseComponent.get_instances(),[c1,c2])

    def test_get_instances_subclass(self):
        class MyComponent(Component):
            pass
        class MyOtherComponent(MyComponent):
            pass
        c1 = MyComponent(None)
        c2 = MyOtherComponent(c1)
        c3 = MyOtherComponent(c2)
        self.assertEquals(MyComponent.get_instances(), [c1, c2, c3])
        self.assertEquals(MyOtherComponent.get_instances(), [c2, c3])

    def test_get_instances_root(self):
        class MyComponent(Component):
            pass
        class MyOtherComponent(MyComponent):
            pass
        c1 = MyComponent(None)
        c2 = MyOtherComponent(c1)
        c3 = MyOtherComponent(c2)
        c4 = MyComponent(None)
        c5 = MyComponent(c4)
        self.assertEquals(MyComponent.get_instances(root=c1), [c1, c2, c3])
        self.assertEquals(MyComponent.get_instances(root=c4), [c4, c5])


class TestComponent(TestCase):

    def test_parent_child(self):
        c1 = Component(None)
        c2 = Component(c1)
        c3 = Component(c1)
        c4 = Component(c3)
        self.assertEquals(c1.parent, None)
        self.assertEquals(c2.parent, c1)
        self.assertEquals(c3.parent, c1)
        self.assertEquals(c4.parent, c3)
        self.assertEquals(c1.children, [c2, c3])
        self.assertEquals(c2.children, [])
        self.assertEquals(c3.children, [c4])
        self.assertEquals(c4.children, [])

    def test_root(self):
        c1 = Component(None)
        c2 = Component(c1)
        c3 = Component(c1)
        c4 = Component(c3)
        self.assertEquals(c1.root, c1.root)
        self.assertEquals(c2.root, c1)
        self.assertEquals(c3.root, c1)
        self.assertEquals(c4.root, c1)

    def test_change_parent(self):
        c1 = Component(None)
        c2 = Component(None)
        c3 = Component(c1)
        self.assertEquals(c3.root, c1)
        self.assertEquals(c3.parent, c1)
        self.assertEquals(c1.children,[c3])
        c3.parent = c2
        self.assertEquals(c3.root, c2)
        self.assertEquals(c3.parent, c2)
        self.assertEquals(c2.children,[c3])
        self.assertEquals(c1.children,[])

    def test_subclass_parent(self):
        c1 = Component(None)
        self.assertRaises(TraitletError, setattr, c1, 'parent', 10)

        class MyComponent(Component):
            pass
        c1 = Component(None)
        c2 = MyComponent(c1)
        self.assertEquals(MyComponent.parent.this_class, Component)
        self.assertEquals(c2.parent, c1)

    def test_bad_root(self):
        c1 = Component(None)
        c2 = Component(None)
        c3 = Component(None)
        self.assertRaises(ComponentError, setattr, c1, 'root', c2)
        c1.parent = c2
        self.assertEquals(c1.root, c2)
        self.assertRaises(ComponentError, setattr, c1, 'root', c3)


class TestComponentConfig(TestCase):

    def test_default(self):
        c1 = Component(None)
        c2 = Component(c1)
        c3 = Component(c2)
        self.assertEquals(c1.config, c2.config)
        self.assertEquals(c2.config, c3.config)

    def test_custom(self):
        config = Config()
        config.foo = 'foo'
        config.bar = 'bar'
        c1 = Component(None, config=config)
        c2 = Component(c1)
        c3 = Component(c2)
        self.assertEquals(c1.config, config)
        self.assertEquals(c2.config, config)
        self.assertEquals(c3.config, config)
        # Test that we always make copies
        self.assert_(c1.config is not config)
        self.assert_(c2.config is not config)
        self.assert_(c3.config is not config)
        self.assert_(c1.config is not c2.config)
        self.assert_(c2.config is not c3.config)
        
    def test_inheritance(self):
        class MyComponent(Component):
            a = Int(1, config=True)
            b = Float(1.0, config=True)
            c = Str('no config')
        config = Config()
        config.MyComponent.a = 2
        config.MyComponent.b = 2.0
        c1 = MyComponent(None, config=config)
        c2 = MyComponent(c1)
        self.assertEquals(c1.a, config.MyComponent.a)
        self.assertEquals(c1.b, config.MyComponent.b)
        self.assertEquals(c2.a, config.MyComponent.a)
        self.assertEquals(c2.b, config.MyComponent.b)
        c4 = MyComponent(c2, config=Config())
        self.assertEquals(c4.a, 1)
        self.assertEquals(c4.b, 1.0)

    def test_parent(self):
        class Foo(Component):
            a = Int(0, config=True)
            b = Str('nope', config=True)
        class Bar(Foo):
            b = Str('gotit', config=False)
            c = Float(config=True)
        config = Config()
        config.Foo.a = 10
        config.Foo.b = "wow"
        config.Bar.b = 'later'
        config.Bar.c = 100.0
        f = Foo(None, config=config)
        b = Bar(f)
        self.assertEquals(f.a, 10)
        self.assertEquals(f.b, 'wow')
        self.assertEquals(b.b, 'gotit')
        self.assertEquals(b.c, 100.0)


class TestComponentName(TestCase):

    def test_default(self):
        class MyComponent(Component):
            pass
        c1 = Component(None)
        c2 = MyComponent(None)
        c3 = Component(c2)
        self.assertNotEquals(c1.name, c2.name)
        self.assertNotEquals(c1.name, c3.name)

    def test_manual(self):
        class MyComponent(Component):
            pass
        c1 = Component(None, name='foo')
        c2 = MyComponent(None, name='bar')
        c3 = Component(c2, name='bah')
        self.assertEquals(c1.name, 'foo')
        self.assertEquals(c2.name, 'bar')
        self.assertEquals(c3.name, 'bah')
