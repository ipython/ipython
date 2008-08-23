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
    from twisted.application.service import IService
    from IPython.kernel.controllerservice import ControllerService
    from IPython.kernel.tests import multienginetest as met
    from controllertest import IControllerCoreTestCase
    from IPython.testing.util import DeferredTestCase
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")

class BasicControllerServiceTest(DeferredTestCase,
    IControllerCoreTestCase):

    def setUp(self):
        self.controller  = ControllerService()
        self.controller.startService()

    def tearDown(self):
        self.controller.stopService()
