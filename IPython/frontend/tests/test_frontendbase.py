# encoding: utf-8

"""This file contains unittests for the frontendbase module."""

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

import unittest
from IPython.frontend import frontendbase
from IPython.kernel.engineservice import EngineService

class FrontEndCallbackChecker(frontendbase.FrontEndBase):
    """FrontEndBase subclass for checking callbacks"""
    def __init__(self, engine=None, history=None):
        super(FrontEndCallbackChecker, self).__init__(engine=engine, history=history)
        self.updateCalled = False
        self.renderResultCalled = False
        self.renderErrorCalled = False
    
    def update_cell_prompt(self, result):
        self.updateCalled = True
        return result
    
    def render_result(self, result):
        self.renderResultCalled = True
        return result
    
    
    def render_error(self, failure):
        self.renderErrorCalled = True
        return failure
    


    
class TestFrontendBase(unittest.TestCase):
    def setUp(self):
        """Setup the EngineService and FrontEndBase"""
        
        self.fb = FrontEndCallbackChecker(engine=EngineService())
    
    
    def test_implementsIFrontEnd(self):
        assert(frontendbase.IFrontEnd.implementedBy(frontendbase.FrontEndBase))
    
    
    def test_is_completeReturnsFalseForIncompleteBlock(self):
        """"""
        
        block = """def test(a):"""
        
        assert(self.fb.is_complete(block) == False)
    
    def test_is_completeReturnsTrueForCompleteBlock(self):
        """"""
        
        block = """def test(a): pass"""
            
        assert(self.fb.is_complete(block))
        
        block = """a=3"""
        
        assert(self.fb.is_complete(block))
    
    
    def test_blockIDAddedToResult(self):
        block = """3+3"""
        
        d = self.fb.execute(block, blockID='TEST_ID')
        
        d.addCallback(self.checkBlockID, expected='TEST_ID')
    
    def checkBlockID(self, result, expected=""):
        assert(result['blockID'] == expected)
    
    
    def test_callbacksAddedToExecuteRequest(self):
        """test that
        update_cell_prompt
        render_result
        
        are added to execute request
        """
        
        d = self.fb.execute("10+10")
        d.addCallback(self.checkCallbacks)
    
    
    def checkCallbacks(self, result):
        assert(self.fb.updateCalled)
        assert(self.fb.renderResultCalled)
    
    
    def test_errorCallbackAddedToExecuteRequest(self):
        """test that render_error called on execution error"""
        
        d = self.fb.execute("raise Exception()")
        d.addCallback(self.checkRenderError)
    
    def checkRenderError(self, result):
        assert(self.fb.renderErrorCalled)
    
    # TODO: add tests for history
    
