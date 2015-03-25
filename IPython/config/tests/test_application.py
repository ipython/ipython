# coding: utf-8
"""
Tests for IPython.config.application.Application
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import logging
import os
from io import StringIO
from unittest import TestCase

pjoin = os.path.join

import nose.tools as nt

from IPython.config.configurable import Configurable
from IPython.config.loader import Config

from IPython.config.application import (
    Application
)

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import (
    Bool, Unicode, Integer, List, Dict
)


class Foo(Configurable):

    i = Integer(0, config=True, help="The integer i.")
    j = Integer(1, config=True, help="The integer j.")
    name = Unicode(u'Brian', config=True, help="First name.")


class Bar(Configurable):

    b = Integer(0, config=True, help="The integer b.")
    enabled = Bool(True, config=True, help="Enable bar.")


class MyApp(Application):

    name = Unicode(u'myapp')
    running = Bool(False, config=True,
                   help="Is the app running?")
    classes = List([Bar, Foo])
    config_file = Unicode(u'', config=True,
                   help="Load this config file")

    aliases = Dict({
                    'i' : 'Foo.i',
                    'j' : 'Foo.j',
                    'name' : 'Foo.name',
                    'enabled' : 'Bar.enabled',
                    'log-level' : 'Application.log_level',
                })
    
    flags = Dict(dict(enable=({'Bar': {'enabled' : True}}, "Set Bar.enabled to True"),
                  disable=({'Bar': {'enabled' : False}}, "Set Bar.enabled to False"),
                  crit=({'Application' : {'log_level' : logging.CRITICAL}},
                        "set level=CRITICAL"),
            ))
    
    def init_foo(self):
        self.foo = Foo(parent=self)

    def init_bar(self):
        self.bar = Bar(parent=self)


class TestApplication(TestCase):

    def test_log(self):
        stream = StringIO()
        app = MyApp(log_level=logging.INFO)
        handler = logging.StreamHandler(stream)
        # trigger reconstruction of the log formatter
        app.log.handlers = [handler]
        app.log_format = "%(message)s"
        app.log_datefmt = "%Y-%m-%d %H:%M"
        app.log.info("hello")
        nt.assert_in("hello", stream.getvalue())

    def test_basic(self):
        app = MyApp()
        self.assertEqual(app.name, u'myapp')
        self.assertEqual(app.running, False)
        self.assertEqual(app.classes, [MyApp,Bar,Foo])
        self.assertEqual(app.config_file, u'')

    def test_config(self):
        app = MyApp()
        app.parse_command_line(["--i=10","--Foo.j=10","--enabled=False","--log-level=50"])
        config = app.config
        self.assertEqual(config.Foo.i, 10)
        self.assertEqual(config.Foo.j, 10)
        self.assertEqual(config.Bar.enabled, False)
        self.assertEqual(config.MyApp.log_level,50)

    def test_config_propagation(self):
        app = MyApp()
        app.parse_command_line(["--i=10","--Foo.j=10","--enabled=False","--log-level=50"])
        app.init_foo()
        app.init_bar()
        self.assertEqual(app.foo.i, 10)
        self.assertEqual(app.foo.j, 10)
        self.assertEqual(app.bar.enabled, False)

    def test_flags(self):
        app = MyApp()
        app.parse_command_line(["--disable"])
        app.init_bar()
        self.assertEqual(app.bar.enabled, False)
        app.parse_command_line(["--enable"])
        app.init_bar()
        self.assertEqual(app.bar.enabled, True)
    
    def test_aliases(self):
        app = MyApp()
        app.parse_command_line(["--i=5", "--j=10"])
        app.init_foo()
        self.assertEqual(app.foo.i, 5)
        app.init_foo()
        self.assertEqual(app.foo.j, 10)
    
    def test_flag_clobber(self):
        """test that setting flags doesn't clobber existing settings"""
        app = MyApp()
        app.parse_command_line(["--Bar.b=5", "--disable"])
        app.init_bar()
        self.assertEqual(app.bar.enabled, False)
        self.assertEqual(app.bar.b, 5)
        app.parse_command_line(["--enable", "--Bar.b=10"])
        app.init_bar()
        self.assertEqual(app.bar.enabled, True)
        self.assertEqual(app.bar.b, 10)
    
    def test_flatten_flags(self):
        cfg = Config()
        cfg.MyApp.log_level = logging.WARN
        app = MyApp()
        app.update_config(cfg)
        self.assertEqual(app.log_level, logging.WARN)
        self.assertEqual(app.config.MyApp.log_level, logging.WARN)
        app.initialize(["--crit"])
        self.assertEqual(app.log_level, logging.CRITICAL)
        # this would be app.config.Application.log_level if it failed:
        self.assertEqual(app.config.MyApp.log_level, logging.CRITICAL)
    
    def test_flatten_aliases(self):
        cfg = Config()
        cfg.MyApp.log_level = logging.WARN
        app = MyApp()
        app.update_config(cfg)
        self.assertEqual(app.log_level, logging.WARN)
        self.assertEqual(app.config.MyApp.log_level, logging.WARN)
        app.initialize(["--log-level", "CRITICAL"])
        self.assertEqual(app.log_level, logging.CRITICAL)
        # this would be app.config.Application.log_level if it failed:
        self.assertEqual(app.config.MyApp.log_level, "CRITICAL")
    
    def test_extra_args(self):
        app = MyApp()
        app.parse_command_line(["--Bar.b=5", 'extra', "--disable", 'args'])
        app.init_bar()
        self.assertEqual(app.bar.enabled, False)
        self.assertEqual(app.bar.b, 5)
        self.assertEqual(app.extra_args, ['extra', 'args'])
        app = MyApp()
        app.parse_command_line(["--Bar.b=5", '--', 'extra', "--disable", 'args'])
        app.init_bar()
        self.assertEqual(app.bar.enabled, True)
        self.assertEqual(app.bar.b, 5)
        self.assertEqual(app.extra_args, ['extra', '--disable', 'args'])
    
    def test_unicode_argv(self):
        app = MyApp()
        app.parse_command_line(['ünîcødé'])
    
    def test_multi_file(self):
        app = MyApp()
        app.log = logging.getLogger()
        name = 'config.py'
        with TemporaryDirectory('_1') as td1:
            with open(pjoin(td1, name), 'w') as f1:
                f1.write("get_config().MyApp.Bar.b = 1")
            with TemporaryDirectory('_2') as td2:
                with open(pjoin(td2, name), 'w') as f2:
                    f2.write("get_config().MyApp.Bar.b = 2")
                app.load_config_file(name, path=[td2, td1])
                app.init_bar()
                self.assertEqual(app.bar.b, 2)
                app.load_config_file(name, path=[td1, td2])
                app.init_bar()
                self.assertEqual(app.bar.b, 1)

