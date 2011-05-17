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
    Bool, Unicode, Int, Float, List
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class Foo(Configurable):

    i = Int(0, config=True, shortname='i', help="The integer i.")
    j = Int(1, config=True, shortname='j', help="The integer j.")
    name = Unicode(u'Brian', config=True, shortname='name', help="First name.")


class Bar(Configurable):

    enabled = Bool(True, config=True, shortname="enabled", help="Enable bar.")


class MyApp(Application):

    app_name = Unicode(u'myapp')
    running = Bool(False, config=True, shortname="running",
                   help="Is the app running?")
    classes = List([Bar, Foo])
    config_file = Unicode(u'', config=True, shortname="config_file",
                   help="Load this config file")

    def init_foo(self):
        self.foo = Foo(config=self.config)

    def init_bar(self):
        self.bar = Bar(config=self.config)


class TestApplication(TestCase):

    def test_basic(self):
        app = MyApp()
        self.assertEquals(app.app_name, u'myapp')
        self.assertEquals(app.running, False)
        self.assertEquals(app.classes, [MyApp,Bar,Foo])
        self.assertEquals(app.config_file, u'')

    def test_config(self):
        app = MyApp()
        app.parse_command_line(["i=10","Foo.j=10","enabled=False","log_level=0"])
        config = app.config
        self.assertEquals(config.Foo.i, 10)
        self.assertEquals(config.Foo.j, 10)
        self.assertEquals(config.Bar.enabled, False)
        self.assertEquals(config.MyApp.log_level,0)

    def test_config_propagation(self):
        app = MyApp()
        app.parse_command_line(["i=10","Foo.j=10","enabled=False","log_level=0"])
        app.init_foo()
        app.init_bar()
        self.assertEquals(app.foo.i, 10)
        self.assertEquals(app.foo.j, 10)
        self.assertEquals(app.bar.enabled, False)

