# encoding: utf-8
"""
Tests for decorators_trial.py
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

# Tell nose to skip this module
__test__ = {}

import os
import sys

from twisted.trial import unittest
import IPython.testing.decorators_trial as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestDecoratorsTrial(unittest.TestCase):
    
    @dec.skip()
    def test_deliberately_broken(self):
        """A deliberately broken test - we want to skip this one."""
        1/0

    @dec.skip('Testing the skip decorator')
    def test_deliberately_broken2(self):
        """Another deliberately broken test - we want to skip this one."""
        1/0

    @dec.skip_linux
    def test_linux(self):
        self.assertNotEquals(sys.platform,'linux2',"This test can't run under linux")

    @dec.skip_win32
    def test_win32(self):
        self.assertNotEquals(sys.platform,'win32',"This test can't run under windows")

    @dec.skip_osx
    def test_osx(self):
        self.assertNotEquals(sys.platform,'darwin',"This test can't run under osx")
