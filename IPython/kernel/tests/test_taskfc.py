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

import time

from twisted.internet import defer, reactor

from IPython.kernel.fcutil import Tub, UnauthenticatedTub

from IPython.kernel import task as taskmodule
from IPython.kernel import controllerservice as cs
import IPython.kernel.multiengine as me
from IPython.testutils.util import DeferredTestCase
from IPython.kernel.multienginefc import IFCSynchronousMultiEngine
from IPython.kernel.taskfc import IFCTaskController
from IPython.kernel.util import printer
from IPython.kernel.tests.tasktest import ITaskControllerTestCase
from IPython.kernel.clientconnector import ClientConnector

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

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

