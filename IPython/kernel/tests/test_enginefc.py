# encoding: utf-8

"""This file contains unittests for the enginepb.py module."""

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
    from twisted.python import components
    from twisted.internet import reactor, defer
    from twisted.spread import pb
    from twisted.internet.base import DelayedCall
    DelayedCall.debug = True

    import zope.interface as zi

    from IPython.kernel.fcutil import Tub, UnauthenticatedTub
    from IPython.kernel import engineservice as es
    from IPython.testing.util import DeferredTestCase
    from IPython.kernel.controllerservice import IControllerBase
    from IPython.kernel.enginefc import FCRemoteEngineRefFromService, IEngineBase
    from IPython.kernel.engineservice import IEngineQueued
    from IPython.kernel.engineconnector import EngineConnector
    
    from IPython.kernel.tests.engineservicetest import \
        IEngineCoreTestCase, \
        IEngineSerializedTestCase, \
        IEngineQueuedTestCase
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")


class EngineFCTest(DeferredTestCase, 
                 IEngineCoreTestCase, 
                 IEngineSerializedTestCase,
                 IEngineQueuedTestCase
                 ):
 
  zi.implements(IControllerBase)
 
  def setUp(self):
 
      # Start a server and append to self.servers
      self.controller_reference = FCRemoteEngineRefFromService(self)
      self.controller_tub = Tub()
      self.controller_tub.listenOn('tcp:10105:interface=127.0.0.1')
      self.controller_tub.setLocation('127.0.0.1:10105')
     
      furl = self.controller_tub.registerReference(self.controller_reference)
      self.controller_tub.startService()
     
      # Start an EngineService and append to services/client
      self.engine_service = es.EngineService()
      self.engine_service.startService()
      self.engine_tub = Tub()
      self.engine_tub.startService()
      engine_connector = EngineConnector(self.engine_tub)
      d = engine_connector.connect_to_controller(self.engine_service, furl)
      # This deferred doesn't fire until after register_engine has returned and
      # thus, self.engine has been defined and the tets can proceed.
      return d
 
  def tearDown(self):
      dlist = []
      # Shut down the engine
      d = self.engine_tub.stopService()
      dlist.append(d)
      # Shut down the controller
      d = self.controller_tub.stopService()
      dlist.append(d)
      return defer.DeferredList(dlist)
 
  #---------------------------------------------------------------------------
  # Make me look like a basic controller
  #---------------------------------------------------------------------------
 
  def register_engine(self, engine_ref, id=None, ip=None, port=None, pid=None):
      self.engine = IEngineQueued(IEngineBase(engine_ref))
      return {'id':id}
 
  def unregister_engine(self, id):
      pass