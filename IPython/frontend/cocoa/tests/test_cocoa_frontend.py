# encoding: utf-8
"""This file contains unittests for the ipython1.frontend.cocoa.cocoa_frontend module.

Things that should be tested:

 - IPythonCocoaController instantiates an IEngineInteractive
 - IPythonCocoaController executes code on the engine
 - IPythonCocoaController returns continuation for incomplete code
 - IPythonCocoaController returns failure for exceptions raised in executed code
 - IPythonCocoaController mirrors engine's user_ns
"""
__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
from IPython.kernel.core.interpreter import Interpreter
import IPython.kernel.engineservice as es
from IPython.testing.util import DeferredTestCase
from twisted.internet.defer import succeed
from IPython.frontend.cocoa.cocoa_frontend import IPythonCocoaController
                                                    
from Foundation import NSMakeRect
from AppKit import NSTextView, NSScrollView                                                

class TestIPythonCocoaControler(DeferredTestCase):
    """Tests for IPythonCocoaController"""
    
    def setUp(self):
        self.controller = IPythonCocoaController.alloc().init()
        self.engine = es.EngineService()
        self.engine.startService()
    
    
    def tearDown(self):
        self.controller = None
        self.engine.stopService()
    
    def testControllerExecutesCode(self):
        code ="""5+5"""
        expected = Interpreter().execute(code)
        del expected['number']
        def removeNumberAndID(result):
            del result['number']
            del result['id']
            return result
        self.assertDeferredEquals(self.controller.execute(code).addCallback(removeNumberAndID), expected)
    
    def testControllerMirrorsUserNSWithValuesAsStrings(self):
        code = """userns1=1;userns2=2"""
        def testControllerUserNS(result):
            self.assertEquals(self.controller.userNS['userns1'], 1)
            self.assertEquals(self.controller.userNS['userns2'], 2)
        
        self.controller.execute(code).addCallback(testControllerUserNS)
    
    
    def testControllerInstantiatesIEngine(self):
        self.assert_(es.IEngineBase.providedBy(self.controller.engine))
    
    def testControllerCompletesToken(self):
        code = """longNameVariable=10"""
        def testCompletes(result):
            self.assert_("longNameVariable" in result)
        
        def testCompleteToken(result):
            self.controller.complete("longNa").addCallback(testCompletes)
        
        self.controller.execute(code).addCallback(testCompletes)
    
