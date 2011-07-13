"""
Tests for IPython.config.application.Application

Authors:

* Brian Granger
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

from IPython.config.configurable import Configurable

from IPython.config.application import (
    Application
)

from IPython.utils.traitlets import (
    Bool, Unicode, Int, Float, List, Dict
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class Foo(Configurable):

    i = Int(0, config=True, help="The integer i.")
    j = Int(1, config=True, help="The integer j.")
    name = Unicode(u'Brian', config=True, help="First name.")


class Bar(Configurable):

    b = Int(0, config=True, help="The integer b.")
    enabled = Bool(True, config=True, help="Enable bar.")


class MyApp(Application):

    name = Unicode(u'myapp')
    running = Bool(False, config=True,
                   help="Is the app running?")
    classes = List([Bar, Foo])
    config_file = Unicode(u'', config=True,
                   help="Load this config file")

    aliases = Dict(dict(i='Foo.i',j='Foo.j',name='Foo.name',
                    enabled='Bar.enabled', log_level='MyApp.log_level'))
    
    flags = Dict(dict(enable=({'Bar': {'enabled' : True}}, "Set Bar.enabled to True"),
                  disable=({'Bar': {'enabled' : False}}, "Set Bar.enabled to False")))
    
    def init_foo(self):
        self.foo = Foo(config=self.config)

    def init_bar(self):
        self.bar = Bar(config=self.config)


class TestApplication(TestCase):

    def test_basic(self):
        app = MyApp()
        self.assertEquals(app.name, u'myapp')
        self.assertEquals(app.running, False)
        self.assertEquals(app.classes, [MyApp,Bar,Foo])
        self.assertEquals(app.config_file, u'')

    def test_config(self):
        app = MyApp()
        app.parse_command_line(["--i=10","--Foo.j=10","--enabled=False","--log_level=50"])
        config = app.config
        self.assertEquals(config.Foo.i, 10)
        self.assertEquals(config.Foo.j, 10)
        self.assertEquals(config.Bar.enabled, False)
        self.assertEquals(config.MyApp.log_level,50)

    def test_config_propagation(self):
        app = MyApp()
        app.parse_command_line(["--i=10","--Foo.j=10","--enabled=False","--log_level=50"])
        app.init_foo()
        app.init_bar()
        self.assertEquals(app.foo.i, 10)
        self.assertEquals(app.foo.j, 10)
        self.assertEquals(app.bar.enabled, False)

    def test_flags(self):
        app = MyApp()
        app.parse_command_line(["--disable"])
        app.init_bar()
        self.assertEquals(app.bar.enabled, False)
        app.parse_command_line(["--enable"])
        app.init_bar()
        self.assertEquals(app.bar.enabled, True)
    
    def test_aliases(self):
        app = MyApp()
        app.parse_command_line(["--i=5", "--j=10"])
        app.init_foo()
        self.assertEquals(app.foo.i, 5)
        app.init_foo()
        self.assertEquals(app.foo.j, 10)
    
    def test_flag_clobber(self):
        """test that setting flags doesn't clobber existing settings"""
        app = MyApp()
        app.parse_command_line(["--Bar.b=5", "--disable"])
        app.init_bar()
        self.assertEquals(app.bar.enabled, False)
        self.assertEquals(app.bar.b, 5)
        app.parse_command_line(["--enable", "--Bar.b=10"])
        app.init_bar()
        self.assertEquals(app.bar.enabled, True)
        self.assertEquals(app.bar.b, 10)
    
    def test_extra_args(self):
        app = MyApp()
        app.parse_command_line(["--Bar.b=5", 'extra', "--disable", 'args'])
        app.init_bar()
        self.assertEquals(app.bar.enabled, False)
        self.assertEquals(app.bar.b, 5)
        self.assertEquals(app.extra_args, ['extra', 'args'])
        app = MyApp()
        app.parse_command_line(["--Bar.b=5", '--', 'extra', "--disable", 'args'])
        app.init_bar()
        self.assertEquals(app.bar.enabled, True)
        self.assertEquals(app.bar.b, 5)
        self.assertEquals(app.extra_args, ['extra', '--disable', 'args'])
    

