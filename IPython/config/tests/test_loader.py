#!/usr/bin/env python
# encoding: utf-8
"""
Tests for IPython.config.loader

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

import os
from tempfile import mkstemp
from unittest import TestCase

from IPython.config.loader import PyFileConfigLoader, ArgParseConfigLoader

#-----------------------------------------------------------------------------
# Actual tests
#-----------------------------------------------------------------------------


pyfile = """
A = 10
B = range(10)
C = True
D = 'hi there'
"""

class TestPyFileCL(TestCase):

    def test_basic(self):
        fd, fname = mkstemp()
        f = os.fdopen(fd, 'w')
        f.write(pyfile)
        f.close()
        cl = PyFileConfigLoader(fname)
        config = cl.load_config()
        self.assertEquals(config.A, 10)
        self.assertEquals(config.B, range(10))
        self.assertEquals(config.C, True)
        self.assertEquals(config.D, 'hi there')


class TestArgParseCL(TestCase):

    def test_basic(self):

        class MyLoader(ArgParseConfigLoader):
            arguments = [
                (('-f','--foo'), dict(dest='FOO', type=str)),
                (('-b',), dict(dest='BAR', type=int)),
                (('-n',), dict(dest='N', action='store_true')),
                (('BAM',), dict(type=str))
            ]

        cl = MyLoader()
        config = cl.load_config('-f hi -b 10 -n wow'.split())
        self.assertEquals(config.FOO, 'hi')
        self.assertEquals(config.BAR, 10)
        self.assertEquals(config.N, True)
        self.assertEquals(config.BAM, 'wow')

    def test_add_arguments(self):

        class MyLoader(ArgParseConfigLoader):
            def _add_arguments(self):
                subparsers = self.parser.add_subparsers(dest='subparser_name')
                subparser1 = subparsers.add_parser('1')
                subparser1.add_argument('-x')
                subparser2 = subparsers.add_parser('2')
                subparser2.add_argument('y')

        cl = MyLoader()
        config = cl.load_config('2 frobble'.split())
        self.assertEquals(config.subparser_name, '2')
        self.assertEquals(config.y, 'frobble')
        config = cl.load_config('1 -x frobble'.split())
        self.assertEquals(config.subparser_name, '1')
        self.assertEquals(config.x, 'frobble')

