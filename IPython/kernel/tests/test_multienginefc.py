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
    from twisted.internet import defer, reactor

    from IPython.kernel.fcutil import Tub, UnauthenticatedTub

    from IPython.testing.util import DeferredTestCase
    from IPython.kernel.controllerservice import ControllerService
    from IPython.kernel.multiengine import IMultiEngine
    from IPython.kernel.tests.multienginetest import IFullSynchronousMultiEngineTestCase
    from IPython.kernel.multienginefc import IFCSynchronousMultiEngine
    from IPython.kernel import multiengine as me
    from IPython.kernel.clientconnector import ClientConnector
    from IPython.kernel.parallelfunction import ParallelFunction
    from IPython.kernel.error import CompositeError
    from IPython.kernel.util import printer
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")
    
def _raise_it(f):
    try:
        f.raiseException()
    except CompositeError, e:
        e.raise_exception()


class FullSynchronousMultiEngineTestCase(DeferredTestCase, IFullSynchronousMultiEngineTestCase):

    def setUp(self):
    
        self.engines = []
            
        self.controller = ControllerService()
        self.controller.startService()
        self.imultiengine = IMultiEngine(self.controller)
        self.mec_referenceable = IFCSynchronousMultiEngine(self.imultiengine)

        self.controller_tub = Tub()
        self.controller_tub.listenOn('tcp:10105:interface=127.0.0.1')
        self.controller_tub.setLocation('127.0.0.1:10105')
    
        furl = self.controller_tub.registerReference(self.mec_referenceable)
        self.controller_tub.startService()
    
        self.client_tub = ClientConnector()
        d = self.client_tub.get_multiengine_client(furl)
        d.addCallback(self.handle_got_client)
        return d
    
    def handle_got_client(self, client):
        self.multiengine = client

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
        self.addEngine(4)
        m = self.multiengine.mapper()
        self.assertEquals(m.multiengine,self.multiengine)
        self.assertEquals(m.dist,'b')
        self.assertEquals(m.targets,'all')
        self.assertEquals(m.block,True)
    
    def test_map_default(self):
        self.addEngine(4)
        m = self.multiengine.mapper()
        d = m.map(lambda x: 2*x, range(10))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        d.addCallback(lambda _: self.multiengine.map(lambda x: 2*x, range(10)))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        return d
    
    def test_map_noblock(self):
        self.addEngine(4)
        m = self.multiengine.mapper(block=False)
        d = m.map(lambda x: 2*x, range(10))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        return d
            
    def test_mapper_fail(self):
        self.addEngine(4)
        m = self.multiengine.mapper()
        d = m.map(lambda x: 1/0, range(10))
        d.addBoth(lambda f: self.assertRaises(ZeroDivisionError, _raise_it, f))
        return d
    
    def test_parallel(self):
        self.addEngine(4)
        p = self.multiengine.parallel()
        self.assert_(isinstance(p, ParallelFunction))
        @p
        def f(x): return 2*x
        d = f(range(10))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        return d
    
    def test_parallel_noblock(self):
        self.addEngine(1)
        p = self.multiengine.parallel(block=False)
        self.assert_(isinstance(p, ParallelFunction))
        @p
        def f(x): return 2*x
        d = f(range(10))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r,[2*x for x in range(10)]))
        return d
    
    def test_parallel_fail(self):
        self.addEngine(4)
        p = self.multiengine.parallel()
        self.assert_(isinstance(p, ParallelFunction))
        @p
        def f(x): return 1/0
        d = f(range(10))
        d.addBoth(lambda f: self.assertRaises(ZeroDivisionError, _raise_it, f))
        return d