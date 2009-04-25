#!/usr/bin/env python
# encoding: utf-8

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Tell nose to skip this module
__test__ = {}

import tempfile
import os, sys

from twisted.internet import reactor
from twisted.trial import unittest

from IPython.kernel.error import FileTimeoutError
from IPython.kernel.twistedutil import wait_for_file

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class TestWaitForFile(unittest.TestCase):

    def test_delay(self):
        filename = tempfile.mktemp()
        def _create_file():
            open(filename,'w').write('####')
        dcall = reactor.callLater(0.5, _create_file)
        d = wait_for_file(filename,delay=0.1)
        d.addCallback(lambda r: self.assert_(r))
        def _cancel_dcall(r):
            if dcall.active():
                dcall.cancel()
        d.addCallback(_cancel_dcall)
        return d
    
    def test_timeout(self):
        filename = tempfile.mktemp()
        d = wait_for_file(filename,delay=0.1,max_tries=1)
        d.addErrback(lambda f: self.assertRaises(FileTimeoutError,f.raiseException))
        return d
        