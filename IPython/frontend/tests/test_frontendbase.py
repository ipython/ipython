# encoding: utf-8

"""This file contains unittests for the frontendbase module."""

__docformat__ = "restructuredtext en"

#---------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team                         
#                                                                           
#  Distributed under the terms of the BSD License.  The full license is in  
#  the file COPYING, distributed as part of this software.                  
#---------------------------------------------------------------------------
                                                                            
#---------------------------------------------------------------------------
# Imports                                                                   
#---------------------------------------------------------------------------

import unittest

try:
    from IPython.frontend.asyncfrontendbase import AsyncFrontEndBase
    from IPython.frontend import frontendbase 
    from IPython.kernel.engineservice import EngineService
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")

from IPython.testing.decorators import skip

class FrontEndCallbackChecker(AsyncFrontEndBase):
    """FrontEndBase subclass for checking callbacks"""
    def __init__(self, engine=None, history=None):
        super(FrontEndCallbackChecker, self).__init__(engine=engine, 
                                                    history=history)
        self.updateCalled = False
        self.renderResultCalled = False
        self.renderErrorCalled = False
   
    def update_cell_prompt(self, result, blockID=None):
        self.updateCalled = True
        return result
   
    def render_result(self, result):
        self.renderResultCalled = True
        return result
    
    
    def render_error(self, failure):
        self.renderErrorCalled = True
        return failure
    


    
class TestAsyncFrontendBase(unittest.TestCase):
    def setUp(self):
        """Setup the EngineService and FrontEndBase"""
        
        self.fb = FrontEndCallbackChecker(engine=EngineService())
    
    def test_implements_IFrontEnd(self):
        assert(frontendbase.IFrontEnd.implementedBy(
                                    AsyncFrontEndBase))
    
    def test_is_complete_returns_False_for_incomplete_block(self):
        """"""
        
        block = """def test(a):"""
        
        assert(self.fb.is_complete(block) == False)
    
    def test_is_complete_returns_True_for_complete_block(self):
        """"""
        
        block = """def test(a): pass"""
            
        assert(self.fb.is_complete(block))
        
        block = """a=3"""
        
        assert(self.fb.is_complete(block))
    
    def test_blockID_added_to_result(self):
        block = """3+3"""
        
        d = self.fb.execute(block, blockID='TEST_ID')
        
        d.addCallback(self.checkBlockID, expected='TEST_ID')
    
    def test_blockID_added_to_failure(self):
        block = "raise Exception()"
        
        d = self.fb.execute(block,blockID='TEST_ID')
        d.addErrback(self.checkFailureID, expected='TEST_ID')
    
    def checkBlockID(self, result, expected=""):
        assert(result['blockID'] == expected)
    
    
    def checkFailureID(self, failure, expected=""):
        assert(failure.blockID == expected)
    
    
    def test_callbacks_added_to_execute(self):
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
    
    @skip("This test fails and lead to an unhandled error in a Deferred.")
    def test_error_callback_added_to_execute(self):
        """test that render_error called on execution error"""
        
        d = self.fb.execute("raise Exception()")
        d.addCallback(self.checkRenderError)
    
    def checkRenderError(self, result):
        assert(self.fb.renderErrorCalled)
    
    def test_history_returns_expected_block(self):
        """Make sure history browsing doesn't fail"""
        
        blocks = ["a=1","a=2","a=3"]
        for b in blocks:
            d = self.fb.execute(b)
        
        # d is now the deferred for the last executed block
        d.addCallback(self.historyTests, blocks)
        
    
    def historyTests(self, result, blocks):
        """historyTests"""
        
        assert(len(blocks) >= 3)
        assert(self.fb.get_history_previous("") == blocks[-2])
        assert(self.fb.get_history_previous("") == blocks[-3])
        assert(self.fb.get_history_next() == blocks[-2])
    
    
    def test_history_returns_none_at_startup(self):
        """test_history_returns_none_at_startup"""
        
        assert(self.fb.get_history_previous("")==None)
        assert(self.fb.get_history_next()==None)
    
    
