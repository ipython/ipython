# encoding: utf-8

"""This file contains unittests for the kernel.task.py module."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

try:
    import time

    from twisted.internet import defer
    from twisted.trial import unittest

    from IPython.kernel import task, controllerservice as cs, engineservice as es
    from IPython.kernel.multiengine import IMultiEngine
    from IPython.testing.util import DeferredTestCase
    from IPython.kernel.tests.tasktest import ITaskControllerTestCase
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

class BasicTaskControllerTestCase(DeferredTestCase, ITaskControllerTestCase):

    def setUp(self):
        self.controller  = cs.ControllerService()
        self.controller.startService()
        self.multiengine = IMultiEngine(self.controller)
        self.tc = task.ITaskController(self.controller)
        self.tc.failurePenalty = 0
        self.engines=[]
    
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()


