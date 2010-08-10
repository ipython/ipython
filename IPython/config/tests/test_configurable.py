#!/usr/bin/env python
# encoding: utf-8
"""
Tests for IPython.config.configurable

Authors:

* Brian Granger
* Fernando Perez (design help)
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from unittest import TestCase

from IPython.config.configurable import Configurable, ConfigurableError
from IPython.utils.traitlets import (
    TraitError, Int, Float, Str
)
from IPython.config.loader import Config


#-----------------------------------------------------------------------------
# Test cases
#-----------------------------------------------------------------------------


class TestConfigurableConfig(TestCase):

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
        c2 = Configurable(c1.config)
        c3 = Configurable(c2.config)
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
        class MyConfigurable(Configurable):
            a = Int(1, config=True)
            b = Float(1.0, config=True)
            c = Str('no config')
        config = Config()
        config.MyConfigurable.a = 2
        config.MyConfigurable.b = 2.0
        c1 = MyConfigurable(config=config)
        c2 = MyConfigurable(c1.config)
        self.assertEquals(c1.a, config.MyConfigurable.a)
        self.assertEquals(c1.b, config.MyConfigurable.b)
        self.assertEquals(c2.a, config.MyConfigurable.a)
        self.assertEquals(c2.b, config.MyConfigurable.b)

    def test_parent(self):
        class Foo(Configurable):
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
        f = Foo(config=config)
        b = Bar(f.config)
        self.assertEquals(f.a, 10)
        self.assertEquals(f.b, 'wow')
        self.assertEquals(b.b, 'gotit')
        self.assertEquals(b.c, 100.0)
