# encoding: utf-8
"""This file contains unittests for the
IPython.frontend.cocoa.cocoa_frontend module.
"""
__docformat__ = "restructuredtext en"

#---------------------------------------------------------------------------
#       Copyright (C) 2005-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Imports
#---------------------------------------------------------------------------

# Tell nose to skip this module
__test__ = {}

from twisted.trial import unittest
from twisted.internet.defer import succeed

from IPython.kernel.core.interpreter import Interpreter
import IPython.kernel.engineservice as es

try:
    from IPython.frontend.cocoa.cocoa_frontend import IPythonCocoaController
    from Foundation import NSMakeRect
    from AppKit import NSTextView, NSScrollView
except ImportError:
    # This tells twisted.trial to skip this module if PyObjC is not found
    skip = True

#---------------------------------------------------------------------------
# Tests
#---------------------------------------------------------------------------
class TestIPythonCocoaControler(unittest.TestCase):
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
        d = self.controller.execute(code)
        d.addCallback(removeNumberAndID)
        d.addCallback(lambda r: self.assertEquals(r, expected))

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


    def testCurrentIndent(self):
        """test that current_indent_string returns current indent or None.
        Uses _indent_for_block for direct unit testing.
        """

        self.controller.tabUsesSpaces = True
        self.assert_(self.controller._indent_for_block("""a=3""") == None)
        self.assert_(self.controller._indent_for_block("") == None)
        block = """def test():\n    a=3"""
        self.assert_(self.controller._indent_for_block(block) == \
                    ' ' * self.controller.tabSpaces)

        block = """if(True):\n%sif(False):\n%spass""" % \
                    (' '*self.controller.tabSpaces,
                     2*' '*self.controller.tabSpaces)
        self.assert_(self.controller._indent_for_block(block) == \
                    2*(' '*self.controller.tabSpaces))

