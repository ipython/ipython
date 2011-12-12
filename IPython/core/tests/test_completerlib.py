# -*- coding: utf-8 -*-
"""Tests for completerlib.

"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import shutil
import sys
import tempfile
import unittest
from os.path import join

import nose.tools as nt
from nose import SkipTest

from IPython.core.completerlib import magic_run_completer
from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils import py3compat


class MockEvent(object):
    def __init__(self, line):
        self.line = line

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------
class Test_magic_run_completer(unittest.TestCase):
    def setUp(self):
        self.BASETESTDIR = tempfile.mkdtemp()
        for fil in [u"aaø.py", u"a.py", u"b.py"]:
            with open(join(self.BASETESTDIR, fil), "w") as sfile:
                sfile.write("pass\n")
        self.oldpath = os.getcwdu()
        os.chdir(self.BASETESTDIR)

    def tearDown(self):
        os.chdir(self.oldpath)
        shutil.rmtree(self.BASETESTDIR)

    def test_1(self):
        """Test magic_run_completer, should match two alterntives
        """
        event = MockEvent(u"%run a")
        mockself = None
        match = set(magic_run_completer(mockself, event))
        self.assertEqual(match, set([u"a.py", u"aaø.py"]))

    def test_2(self):
        """Test magic_run_completer, should match one alterntive
        """
        event = MockEvent(u"%run aa")
        mockself = None
        match = set(magic_run_completer(mockself, event))
        self.assertEqual(match, set([u"aaø.py"]))

    def test_3(self):
        """Test magic_run_completer with unterminated " """
        event = MockEvent(u'%run "a')
        mockself = None
        match = set(magic_run_completer(mockself, event))
        self.assertEqual(match, set([u"a.py", u"aaø.py"]))

