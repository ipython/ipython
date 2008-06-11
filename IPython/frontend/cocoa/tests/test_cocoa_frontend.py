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
from ipython1.core.interpreter import Interpreter
from ipython1.testutils.parametric import Parametric, parametric
from ipython1.core.interpreter import COMPILER_ERROR, INCOMPLETE_INPUT,\
                                        COMPLETE_INPUT
import ipython1.kernel.engineservice as es
from ipython1.testutils.util import DeferredTestCase
from twisted.internet.defer import succeed
from ipython1.frontend.cocoa.cocoa_frontend import IPythonCocoaController,\
                                                    IPythonCLITextViewDelegate,\
                                                    CompilerError
                                                    

class TestIPythonCocoaControler(DeferredTestCase):
    """Tests for IPythonCocoaController"""
    
    def setUp(self):
        self.controller = IPythonCocoaController.alloc().init()
        self.controller.awakeFromNib()
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
        self.assertDeferredEquals(self.controller.executeRequest([code]).addCallback(removeNumberAndID), expected)
    
    def testControllerReturnsNoneForIncompleteCode(self):
        code = """def test(a):"""
        expected = None
        self.assertDeferredEquals(self.controller.executeRequest([code]), expected)
    
    
    def testControllerRaisesCompilerErrorForIllegalCode(self):
        """testControllerRaisesCompilerErrorForIllegalCode"""
        
        code = """def test() pass"""
        self.assertDeferredRaises(self.controller.executeRequest([code]), CompilerError)
    
    def testControllerMirrorsUserNSWithValuesAsStrings(self):
        code = """userns1=1;userns2=2"""
        def testControllerUserNS(result):
            self.assertEquals(self.controller.userNS['userns1'], str(1))
            self.assertEquals(self.controller.userNS['userns2'], str(2))
        
        self.controller.executeRequest([code]).addCallback(testControllerUserNS)
    
    
    def testControllerInstantiatesIEngine(self):
        self.assert_(es.IEngine.providedBy(self.controller.engine))
    
    def testControllerCompletesToken(self):
        code = """longNameVariable=10"""
        def testCompletes(result):
            self.assert_("longNameVariable" in result)
        
        def testCompleteToken(result):
            self.controller.complete("longNa").addCallback(testCompletes)
        
        self.controller.executeRequest([code]).addCallback(testCompletes)
    

Parametric(TestIPythonCocoaControler)