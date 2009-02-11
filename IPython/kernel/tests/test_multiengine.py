# encoding: utf-8

""""""

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
    from twisted.internet import defer
    from IPython.testing.util import DeferredTestCase
    from IPython.kernel.controllerservice import ControllerService
    from IPython.kernel import multiengine as me
    from IPython.kernel.tests.multienginetest import (IMultiEngineTestCase,
        ISynchronousMultiEngineTestCase)
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")

 
class BasicMultiEngineTestCase(DeferredTestCase, IMultiEngineTestCase):

    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        self.multiengine = me.IMultiEngine(self.controller)
        self.engines = []
    
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()


class SynchronousMultiEngineTestCase(DeferredTestCase, ISynchronousMultiEngineTestCase):

    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        self.multiengine = me.ISynchronousMultiEngine(me.IMultiEngine(self.controller))
        self.engines = []
    
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()

