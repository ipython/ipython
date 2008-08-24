# encoding: utf-8

"""This file contains unittests for the kernel.engineservice.py module.

Things that should be tested:

 - Should the EngineService return Deferred objects?
 - Run the same tests that are run in shell.py.
 - Make sure that the Interface is really implemented.
 - The startService and stopService methods.
"""

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
    from twisted.application.service import IService
    
    from IPython.kernel import engineservice as es
    from IPython.testing.util import DeferredTestCase
    from IPython.kernel.tests.engineservicetest import \
        IEngineCoreTestCase, \
        IEngineSerializedTestCase, \
        IEngineQueuedTestCase, \
        IEnginePropertiesTestCase
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")    


class BasicEngineServiceTest(DeferredTestCase,
                             IEngineCoreTestCase, 
                             IEngineSerializedTestCase,
                             IEnginePropertiesTestCase):

    def setUp(self):
        self.engine = es.EngineService()
        self.engine.startService()

    def tearDown(self):
        return self.engine.stopService()

class ThreadedEngineServiceTest(DeferredTestCase,
                             IEngineCoreTestCase, 
                             IEngineSerializedTestCase,
                             IEnginePropertiesTestCase):

    def setUp(self):
        self.engine = es.ThreadedEngineService()
        self.engine.startService()

    def tearDown(self):
        return self.engine.stopService()

class QueuedEngineServiceTest(DeferredTestCase,
                              IEngineCoreTestCase, 
                              IEngineSerializedTestCase,
                              IEnginePropertiesTestCase,
                              IEngineQueuedTestCase):
                          
    def setUp(self):
        self.rawEngine = es.EngineService()
        self.rawEngine.startService()
        self.engine = es.IEngineQueued(self.rawEngine)
    
    def tearDown(self):
        return self.rawEngine.stopService()


