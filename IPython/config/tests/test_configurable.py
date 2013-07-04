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
        self.assertEqual(c1.config, c2.config)
        self.assertEqual(c2.config, c3.config)

    def test_custom(self):
        config = Config()
        config.foo = 'foo'
        config.bar = 'bar'
        c1 = Configurable(config=config)
        c2 = Configurable(config=c1.config)
        c3 = Configurable(config=c2.config)
        self.assertEqual(c1.config, config)
        self.assertEqual(c2.config, config)
        self.assertEqual(c3.config, config)
        # Test that copies are not made
        self.assertTrue(c1.config is config)
        self.assertTrue(c2.config is config)
        self.assertTrue(c3.config is config)
        self.assertTrue(c1.config is c2.config)
        self.assertTrue(c2.config is c3.config)
        
    def test_inheritance(self):
        config = Config()
        config.MyConfigurable.a = 2
        config.MyConfigurable.b = 2.0
        c1 = MyConfigurable(config=config)
        c2 = MyConfigurable(config=c1.config)
        self.assertEqual(c1.a, config.MyConfigurable.a)
        self.assertEqual(c1.b, config.MyConfigurable.b)
        self.assertEqual(c2.a, config.MyConfigurable.a)
        self.assertEqual(c2.b, config.MyConfigurable.b)

    def test_parent(self):
        config = Config()
        config.Foo.a = 10
        config.Foo.b = "wow"
        config.Bar.b = 'later'
        config.Bar.c = 100.0
        f = Foo(config=config)
        b = Bar(config=f.config)
        self.assertEqual(f.a, 10)
        self.assertEqual(f.b, 'wow')
        self.assertEqual(b.b, 'gotit')
        self.assertEqual(b.c, 100.0)

    def test_override1(self):
        config = Config()
        config.MyConfigurable.a = 2
        config.MyConfigurable.b = 2.0
        c = MyConfigurable(a=3, config=config)
        self.assertEqual(c.a, 3)
        self.assertEqual(c.b, config.MyConfigurable.b)
        self.assertEqual(c.c, 'no config')

    def test_override2(self):
        config = Config()
        config.Foo.a = 1
        config.Bar.b = 'or'  # Up above b is config=False, so this won't do it.
        config.Bar.c = 10.0
        c = Bar(config=config)
        self.assertEqual(c.a, config.Foo.a)
        self.assertEqual(c.b, 'gotit')
        self.assertEqual(c.c, config.Bar.c)
        c = Bar(a=2, b='and', c=20.0, config=config)
        self.assertEqual(c.a, 2)
        self.assertEqual(c.b, 'and')
        self.assertEqual(c.c, 20.0)

    def test_help(self):
        self.assertEqual(MyConfigurable.class_get_help(), mc_help)

    def test_help_inst(self):
        inst = MyConfigurable(a=5, b=4)
        self.assertEqual(MyConfigurable.class_get_help(inst), mc_help_inst)


class TestSingletonConfigurable(TestCase):

    def test_instance(self):
        class Foo(SingletonConfigurable): pass
        self.assertEqual(Foo.initialized(), False)
        foo = Foo.instance()
        self.assertEqual(Foo.initialized(), True)
        self.assertEqual(foo, Foo.instance())
        self.assertEqual(SingletonConfigurable._instance, None)

    def test_inheritance(self):
        class Bar(SingletonConfigurable): pass
        class Bam(Bar): pass
        self.assertEqual(Bar.initialized(), False)
        self.assertEqual(Bam.initialized(), False)
        bam = Bam.instance()
        bam == Bar.instance()
        self.assertEqual(Bar.initialized(), True)
        self.assertEqual(Bam.initialized(), True)
        self.assertEqual(bam, Bam._instance)
        self.assertEqual(bam, Bar._instance)
        self.assertEqual(SingletonConfigurable._instance, None)


class MyParent(Configurable):
    pass

class MyParent2(MyParent):
    pass

class TestParentConfigurable(TestCase):
    
    def test_parent_config(self):
        cfg = Config({
            'MyParent' : {
                'MyConfigurable' : {
                    'b' : 2.0,
                }
            }
        })
        parent = MyParent(config=cfg)
        myc = MyConfigurable(parent=parent)
        self.assertEqual(myc.b, parent.config.MyParent.MyConfigurable.b)

    def test_parent_inheritance(self):
        cfg = Config({
            'MyParent' : {
                'MyConfigurable' : {
                    'b' : 2.0,
                }
            }
        })
        parent = MyParent2(config=cfg)
        myc = MyConfigurable(parent=parent)
        self.assertEqual(myc.b, parent.config.MyParent.MyConfigurable.b)

    def test_multi_parent(self):
        cfg = Config({
            'MyParent2' : {
                'MyParent' : {
                    'MyConfigurable' : {
                        'b' : 2.0,
                    }
                },
                # this one shouldn't count
                'MyConfigurable' : {
                    'b' : 3.0,
                },
            }
        })
        parent2 = MyParent2(config=cfg)
        parent = MyParent(parent=parent2)
        myc = MyConfigurable(parent=parent)
        self.assertEqual(myc.b, parent.config.MyParent2.MyParent.MyConfigurable.b)

    def test_parent_priority(self):
        cfg = Config({
            'MyConfigurable' : {
                'b' : 2.0,
            },
            'MyParent' : {
                'MyConfigurable' : {
                    'b' : 3.0,
                }
            },
            'MyParent2' : {
                'MyConfigurable' : {
                    'b' : 4.0,
                }
            }
        })
        parent = MyParent2(config=cfg)
        myc = MyConfigurable(parent=parent)
        self.assertEqual(myc.b, parent.config.MyParent2.MyConfigurable.b)

    def test_multi_parent_priority(self):
        cfg = Config({
            'MyConfigurable' : {
                'b' : 2.0,
            },
            'MyParent' : {
                'MyConfigurable' : {
                    'b' : 3.0,
                }
            },
            'MyParent2' : {
                'MyConfigurable' : {
                    'b' : 4.0,
                }
            },
            'MyParent2' : {
                'MyParent' : {
                    'MyConfigurable' : {
                        'b' : 5.0,
                    }
                }
            }
        })
        parent2 = MyParent2(config=cfg)
        parent = MyParent2(parent=parent2)
        myc = MyConfigurable(parent=parent)
        self.assertEqual(myc.b, parent.config.MyParent2.MyParent.MyConfigurable.b)

