# encoding: utf-8
"""
Tests for IPython.config.loader

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

import os
import sys
from tempfile import mkstemp
from unittest import TestCase

from nose import SkipTest

from IPython.testing.tools import mute_warn

from IPython.utils.traitlets import Unicode
from IPython.config.configurable import Configurable
from IPython.config.loader import (
    Config,
    PyFileConfigLoader,
    KeyValueConfigLoader,
    ArgParseConfigLoader,
    KVArgParseConfigLoader,
    ConfigError
)

#-----------------------------------------------------------------------------
# Actual tests
#-----------------------------------------------------------------------------


pyfile = """
c = get_config()
c.a=10
c.b=20
c.Foo.Bar.value=10
c.Foo.Bam.value=list(range(10))  # list() is just so it's the same on Python 3
c.D.C.value='hi there'
"""

class TestPyFileCL(TestCase):

    def test_basic(self):
        fd, fname = mkstemp('.py')
        f = os.fdopen(fd, 'w')
        f.write(pyfile)
        f.close()
        # Unlink the file
        cl = PyFileConfigLoader(fname)
        config = cl.load_config()
        self.assertEquals(config.a, 10)
        self.assertEquals(config.b, 20)
        self.assertEquals(config.Foo.Bar.value, 10)
        self.assertEquals(config.Foo.Bam.value, range(10))
        self.assertEquals(config.D.C.value, 'hi there')

class MyLoader1(ArgParseConfigLoader):
    def _add_arguments(self, aliases=None, flags=None):
        p = self.parser
        p.add_argument('-f', '--foo', dest='Global.foo', type=str)
        p.add_argument('-b', dest='MyClass.bar', type=int)
        p.add_argument('-n', dest='n', action='store_true')
        p.add_argument('Global.bam', type=str)

class MyLoader2(ArgParseConfigLoader):
    def _add_arguments(self, aliases=None, flags=None):
        subparsers = self.parser.add_subparsers(dest='subparser_name')
        subparser1 = subparsers.add_parser('1')
        subparser1.add_argument('-x',dest='Global.x')
        subparser2 = subparsers.add_parser('2')
        subparser2.add_argument('y')

class TestArgParseCL(TestCase):

    def test_basic(self):
        cl = MyLoader1()
        config = cl.load_config('-f hi -b 10 -n wow'.split())
        self.assertEquals(config.Global.foo, 'hi')
        self.assertEquals(config.MyClass.bar, 10)
        self.assertEquals(config.n, True)
        self.assertEquals(config.Global.bam, 'wow')
        config = cl.load_config(['wow'])
        self.assertEquals(config.keys(), ['Global'])
        self.assertEquals(config.Global.keys(), ['bam'])
        self.assertEquals(config.Global.bam, 'wow')

    def test_add_arguments(self):
        cl = MyLoader2()
        config = cl.load_config('2 frobble'.split())
        self.assertEquals(config.subparser_name, '2')
        self.assertEquals(config.y, 'frobble')
        config = cl.load_config('1 -x frobble'.split())
        self.assertEquals(config.subparser_name, '1')
        self.assertEquals(config.Global.x, 'frobble')

    def test_argv(self):
        cl = MyLoader1(argv='-f hi -b 10 -n wow'.split())
        config = cl.load_config()
        self.assertEquals(config.Global.foo, 'hi')
        self.assertEquals(config.MyClass.bar, 10)
        self.assertEquals(config.n, True)
        self.assertEquals(config.Global.bam, 'wow')


class TestKeyValueCL(TestCase):
    klass = KeyValueConfigLoader

    def test_basic(self):
        cl = self.klass()
        argv = ['--'+s.strip('c.') for s in pyfile.split('\n')[2:-1]]
        with mute_warn():
            config = cl.load_config(argv)
        self.assertEquals(config.a, 10)
        self.assertEquals(config.b, 20)
        self.assertEquals(config.Foo.Bar.value, 10)
        self.assertEquals(config.Foo.Bam.value, range(10))
        self.assertEquals(config.D.C.value, 'hi there')
    
    def test_expanduser(self):
        cl = self.klass()
        argv = ['--a=~/1/2/3', '--b=~', '--c=~/', '--d="~/"']
        with mute_warn():
            config = cl.load_config(argv)
        self.assertEquals(config.a, os.path.expanduser('~/1/2/3'))
        self.assertEquals(config.b, os.path.expanduser('~'))
        self.assertEquals(config.c, os.path.expanduser('~/'))
        self.assertEquals(config.d, '~/')
    
    def test_extra_args(self):
        cl = self.klass()
        with mute_warn():
            config = cl.load_config(['--a=5', 'b', '--c=10', 'd'])
        self.assertEquals(cl.extra_args, ['b', 'd'])
        self.assertEquals(config.a, 5)
        self.assertEquals(config.c, 10)
        with mute_warn():
            config = cl.load_config(['--', '--a=5', '--c=10'])
        self.assertEquals(cl.extra_args, ['--a=5', '--c=10'])
    
    def test_unicode_args(self):
        cl = self.klass()
        argv = [u'--a=épsîlön']
        with mute_warn():
            config = cl.load_config(argv)
        self.assertEquals(config.a, u'épsîlön')
    
    def test_unicode_bytes_args(self):
        uarg = u'--a=é'
        try:
            barg = uarg.encode(sys.stdin.encoding)
        except (TypeError, UnicodeEncodeError):
            raise SkipTest("sys.stdin.encoding can't handle 'é'")
        
        cl = self.klass()
        with mute_warn():
            config = cl.load_config([barg])
        self.assertEquals(config.a, u'é')
    
    def test_unicode_alias(self):
        cl = self.klass()
        argv = [u'--a=épsîlön']
        with mute_warn():
            config = cl.load_config(argv, aliases=dict(a='A.a'))
        self.assertEquals(config.A.a, u'épsîlön')


class TestArgParseKVCL(TestKeyValueCL):
    klass = KVArgParseConfigLoader

    def test_expanduser2(self):
        cl = self.klass()
        argv = ['-a', '~/1/2/3', '--b', "'~/1/2/3'"]
        with mute_warn():
            config = cl.load_config(argv, aliases=dict(a='A.a', b='A.b'))
        self.assertEquals(config.A.a, os.path.expanduser('~/1/2/3'))
        self.assertEquals(config.A.b, '~/1/2/3')
    
class TestConfig(TestCase):

    def test_setget(self):
        c = Config()
        c.a = 10
        self.assertEquals(c.a, 10)
        self.assertEquals(c.has_key('b'), False)

    def test_auto_section(self):
        c = Config()
        self.assertEquals(c.has_key('A'), True)
        self.assertEquals(c._has_section('A'), False)
        A = c.A
        A.foo = 'hi there'
        self.assertEquals(c._has_section('A'), True)
        self.assertEquals(c.A.foo, 'hi there')
        del c.A
        self.assertEquals(len(c.A.keys()),0)

    def test_merge_doesnt_exist(self):
        c1 = Config()
        c2 = Config()
        c2.bar = 10
        c2.Foo.bar = 10
        c1._merge(c2)
        self.assertEquals(c1.Foo.bar, 10)
        self.assertEquals(c1.bar, 10)
        c2.Bar.bar = 10
        c1._merge(c2)
        self.assertEquals(c1.Bar.bar, 10)

    def test_merge_exists(self):
        c1 = Config()
        c2 = Config()
        c1.Foo.bar = 10
        c1.Foo.bam = 30
        c2.Foo.bar = 20
        c2.Foo.wow = 40
        c1._merge(c2)
        self.assertEquals(c1.Foo.bam, 30)
        self.assertEquals(c1.Foo.bar, 20)
        self.assertEquals(c1.Foo.wow, 40)
        c2.Foo.Bam.bam = 10
        c1._merge(c2)
        self.assertEquals(c1.Foo.Bam.bam, 10)

    def test_deepcopy(self):
        c1 = Config()
        c1.Foo.bar = 10
        c1.Foo.bam = 30
        c1.a = 'asdf'
        c1.b = range(10)
        import copy
        c2 = copy.deepcopy(c1)
        self.assertEquals(c1, c2)
        self.assert_(c1 is not c2)
        self.assert_(c1.Foo is not c2.Foo)

    def test_builtin(self):
        c1 = Config()
        exec 'foo = True' in c1
        self.assertEquals(c1.foo, True)
        self.assertRaises(ConfigError, setattr, c1, 'ValueError', 10)
