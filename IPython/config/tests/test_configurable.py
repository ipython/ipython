# encoding: utf-8
"""
Tests for IPython.config.configurable

Authors:

* Brian Granger
* Fernando Perez (design help)
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

from unittest import TestCase

from IPython.config.configurable import (
    Configurable, 
    SingletonConfigurable
)

from IPython.utils.traitlets import (
    Integer, Float, Unicode
)

from IPython.config.loader import Config
from IPython.utils.py3compat import PY3

#-----------------------------------------------------------------------------
# Test cases
#-----------------------------------------------------------------------------


class MyConfigurable(Configurable):
    a = Integer(1, config=True, help="The integer a.")
    b = Float(1.0, config=True, help="The integer b.")
    c = Unicode('no config')


mc_help=u"""MyConfigurable options
----------------------
--MyConfigurable.a=<Integer>
    Default: 1
    The integer a.
--MyConfigurable.b=<Float>
    Default: 1.0
    The integer b."""

mc_help_inst=u"""MyConfigurable options
----------------------
--MyConfigurable.a=<Integer>
    Current: 5
    The integer a.
--MyConfigurable.b=<Float>
    Current: 4.0
    The integer b."""

# On Python 3, the Integer trait is a synonym for Int
if PY3:
    mc_help = mc_help.replace(u"<Integer>", u"<Int>")
    mc_help_inst = mc_help_inst.replace(u"<Integer>", u"<Int>")

class Foo(Configurable):
    a = Integer(0, config=True, help="The integer a.")
    b = Unicode('nope', config=True)


class Bar(Foo):
    b = Unicode('gotit', config=False, help="The string b.")
    c = Float(config=True, help="The string c.")


class TestConfigurable(TestCase):

    def test_default(self):
        c1 = Configurable()
        c2 = Configurable(config=c1.config)
        c3 = Configurable(config=c2.config)
        self.assertEquals(c1.config, c2.config)
        self.assertEquals(c2.config, c3.config)

    def test_custom(self):
        config = Config()
        config.foo = 'foo'
        config.bar = 'bar'
        c1 = Configurable(config=config)
        c2 = Configurable(config=c1.config)
        c3 = Configurable(config=c2.config)
        self.assertEquals(c1.config, config)
        self.assertEquals(c2.config, config)
        self.assertEquals(c3.config, config)
        # Test that copies are not made
        self.assert_(c1.config is config)
        self.assert_(c2.config is config)
        self.assert_(c3.config is config)
        self.assert_(c1.config is c2.config)
        self.assert_(c2.config is c3.config)
        
    def test_inheritance(self):
        config = Config()
        config.MyConfigurable.a = 2
        config.MyConfigurable.b = 2.0
        c1 = MyConfigurable(config=config)
        c2 = MyConfigurable(config=c1.config)
        self.assertEquals(c1.a, config.MyConfigurable.a)
        self.assertEquals(c1.b, config.MyConfigurable.b)
        self.assertEquals(c2.a, config.MyConfigurable.a)
        self.assertEquals(c2.b, config.MyConfigurable.b)

    def test_parent(self):
        config = Config()
        config.Foo.a = 10
        config.Foo.b = "wow"
        config.Bar.b = 'later'
        config.Bar.c = 100.0
        f = Foo(config=config)
        b = Bar(config=f.config)
        self.assertEquals(f.a, 10)
        self.assertEquals(f.b, 'wow')
        self.assertEquals(b.b, 'gotit')
        self.assertEquals(b.c, 100.0)

    def test_override1(self):
        config = Config()
        config.MyConfigurable.a = 2
        config.MyConfigurable.b = 2.0
        c = MyConfigurable(a=3, config=config)
        self.assertEquals(c.a, 3)
        self.assertEquals(c.b, config.MyConfigurable.b)
        self.assertEquals(c.c, 'no config')

    def test_override2(self):
        config = Config()
        config.Foo.a = 1
        config.Bar.b = 'or'  # Up above b is config=False, so this won't do it.
        config.Bar.c = 10.0
        c = Bar(config=config)
        self.assertEquals(c.a, config.Foo.a)
        self.assertEquals(c.b, 'gotit')
        self.assertEquals(c.c, config.Bar.c)
        c = Bar(a=2, b='and', c=20.0, config=config)
        self.assertEquals(c.a, 2)
        self.assertEquals(c.b, 'and')
        self.assertEquals(c.c, 20.0)

    def test_help(self):
        self.assertEquals(MyConfigurable.class_get_help(), mc_help)

    def test_help_inst(self):
        inst = MyConfigurable(a=5, b=4)
        self.assertEquals(MyConfigurable.class_get_help(inst), mc_help_inst)


class TestSingletonConfigurable(TestCase):

    def test_instance(self):
        from IPython.config.configurable import SingletonConfigurable
        class Foo(SingletonConfigurable): pass
        self.assertEquals(Foo.initialized(), False)
        foo = Foo.instance()
        self.assertEquals(Foo.initialized(), True)
        self.assertEquals(foo, Foo.instance())
        self.assertEquals(SingletonConfigurable._instance, None)

    def test_inheritance(self):
        class Bar(SingletonConfigurable): pass
        class Bam(Bar): pass
        self.assertEquals(Bar.initialized(), False)
        self.assertEquals(Bam.initialized(), False)
        bam = Bam.instance()
        bam == Bar.instance()
        self.assertEquals(Bar.initialized(), True)
        self.assertEquals(Bam.initialized(), True)
        self.assertEquals(bam, Bam._instance)
        self.assertEquals(bam, Bar._instance)
        self.assertEquals(SingletonConfigurable._instance, None)
