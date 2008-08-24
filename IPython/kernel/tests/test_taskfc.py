#!/usr/bin/env python
# encoding: utf-8

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

    from twisted.internet import defer, reactor

    from IPython.kernel.fcutil import Tub, UnauthenticatedTub

    from IPython.kernel import task as taskmodule
    from IPython.kernel import controllerservice as cs
    import IPython.kernel.multiengine as me
    from IPython.testing.util import DeferredTestCase
    from IPython.kernel.multienginefc import IFCSynchronousMultiEngine
    from IPython.kernel.taskfc import IFCTaskController
    from IPython.kernel.util import printer
    from IPython.kernel.tests.tasktest import ITaskControllerTestCase
    from IPython.kernel.clientconnector import ClientConnector
    from IPython.kernel.error import CompositeError
    from IPython.kernel.parallelfunction import ParallelFunction
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")


#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def _raise_it(f):
    try:
        f.raiseException()
    except CompositeError, e:
        e.raise_exception()

class TaskTest(DeferredTestCase, ITaskControllerTestCase):

    def setUp(self):
    
        self.engines = []
            
        self.controller = cs.ControllerService()
        self.controller.startService()
        self.imultiengine = me.IMultiEngine(self.controller)
        self.itc = taskmodule.ITaskController(self.controller)
        self.itc.failurePenalty = 0
    
        self.mec_referenceable = IFCSynchronousMultiEngine(self.imultiengine)
        self.tc_referenceable = IFCTaskController(self.itc)
    
        self.controller_tub = Tub()
        self.controller_tub.listenOn('tcp:10105:interface=127.0.0.1')
        self.controller_tub.setLocation('127.0.0.1:10105')
    
        mec_furl = self.controller_tub.registerReference(self.mec_referenceable)
        tc_furl = self.controller_tub.registerReference(self.tc_referenceable)
        self.controller_tub.startService()
    
        self.client_tub = ClientConnector()
        d = self.client_tub.get_multiengine_client(mec_furl)
        d.addCallback(self.handle_mec_client)
        d.addCallback(lambda _: self.client_tub.get_task_client(tc_furl))
        d.addCallback(self.handle_tc_client)
        return d
    
    def handle_mec_client(self, client):
        self.multiengine = client

    def handle_tc_client(self, client):
        self.tc = client

    def tearDown(self):
        dlist = []
        # Shut down the multiengine client
        d = self.client_tub.tub.stopService()
        dlist.append(d)
        # Shut down the engines
        for e in self.engines:
            e.stopService()
        # Shut down the controller
        d = self.controller_tub.stopService()
        d.addBoth(lambda _: self.controller.stopService())
        dlist.append(d)
        return defer.DeferredList(dlist)
    
    def test_mapper(self):
        self.addEngine(1)
        m = self.tc.mapper()
        self.assertEquals(m.task_controller,self.tc)
        self.assertEquals(m.clear_before,False)
        self.assertEquals(m.clear_after,False)
        self.assertEquals(m.retries,0)
        self.assertEquals(m.recovery_task,None)
        self.assertEquals(m.depend,None)
        self.assertEquals(m.block,True)
    
    def test_map_default(self):
        self.addEngine(1)
        m = self.tc.mapper()
        d = m.map(lambda x: 2*x, range(10))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        d.addCallback(lambda _: self.tc.map(lambda x: 2*x, range(10)))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        return d
    
    def test_map_noblock(self):
        self.addEngine(1)
        m = self.tc.mapper(block=False)
        d = m.map(lambda x: 2*x, range(10))
        d.addCallback(lambda r: self.assertEquals(r,[x for x in range(10)]))
        return d
            
    def test_mapper_fail(self):
        self.addEngine(1)
        m = self.tc.mapper()
        d = m.map(lambda x: 1/0, range(10))
        d.addBoth(lambda f: self.assertRaises(ZeroDivisionError, _raise_it, f))
        return d
    
    def test_parallel(self):
        self.addEngine(1)
        p = self.tc.parallel()
        self.assert_(isinstance(p, ParallelFunction))
        @p
        def f(x): return 2*x
        d = f(range(10))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        return d
    
    def test_parallel_noblock(self):
        self.addEngine(1)
        p = self.tc.parallel(block=False)
        self.assert_(isinstance(p, ParallelFunction))
        @p
        def f(x): return 2*x
        d = f(range(10))
        d.addCallback(lambda r: self.assertEquals(r,[x for x in range(10)]))
        return d
    
    def test_parallel_fail(self):
        self.addEngine(1)
        p = self.tc.parallel()
        self.assert_(isinstance(p, ParallelFunction))
        @p
        def f(x): return 1/0
        d = f(range(10))
        d.addBoth(lambda f: self.assertRaises(ZeroDivisionError, _raise_it, f))
        return d