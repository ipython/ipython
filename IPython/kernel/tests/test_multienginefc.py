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
except ImportError:
    pass
else:
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
