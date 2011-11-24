# encoding: utf-8
"""This file contains unittests for the asyncfrontendbase module."""

#---------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Imports
#---------------------------------------------------------------------------

from twisted.trial import unittest

from IPython.frontend.asyncfrontendbase import AsyncFrontEndBase
from IPython.frontend import frontendbase
from IPython.kernel.engineservice import EngineService
from IPython.testing.parametric import Parametric, parametric

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

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
        self.assert_(frontendbase.IFrontEnd.implementedBy(
                                    AsyncFrontEndBase))

    def test_is_complete_returns_False_for_incomplete_block(self):
        block = """def test(a):"""
        self.assert_(self.fb.is_complete(block) == False)

    def test_is_complete_returns_True_for_complete_block(self):
        block = """def test(a): pass"""
        self.assert_(self.fb.is_complete(block))
        block = """a=3"""
        self.assert_(self.fb.is_complete(block))

    def test_blockID_added_to_result(self):
        block = """3+3"""
        d = self.fb.execute(block, blockID='TEST_ID')
        d.addCallback(lambda r: self.assert_(r['blockID']=='TEST_ID'))
        return d

    def test_blockID_added_to_failure(self):
        block = "raise Exception()"
        d = self.fb.execute(block,blockID='TEST_ID')
        d.addErrback(lambda f: self.assert_(f.blockID=='TEST_ID'))
        return d

    def test_callbacks_added_to_execute(self):
        d = self.fb.execute("10+10")
        d.addCallback(lambda r: self.assert_(self.fb.updateCalled and self.fb.renderResultCalled))
        return d

    def test_error_callback_added_to_execute(self):
        """Test that render_error called on execution error."""

        d = self.fb.execute("raise Exception()")
        d.addErrback(lambda f: self.assert_(self.fb.renderErrorCalled))
        return d

    def test_history_returns_expected_block(self):
        """Make sure history browsing doesn't fail."""

        blocks = ["a=1","a=2","a=3"]
        d = self.fb.execute(blocks[0])
        d.addCallback(lambda _: self.fb.execute(blocks[1]))
        d.addCallback(lambda _: self.fb.execute(blocks[2]))
        d.addCallback(lambda _: self.assert_(self.fb.get_history_previous("")==blocks[-2]))
        d.addCallback(lambda _: self.assert_(self.fb.get_history_previous("")==blocks[-3]))
        d.addCallback(lambda _: self.assert_(self.fb.get_history_next()==blocks[-2]))
        return d

    def test_history_returns_none_at_startup(self):
        self.assert_(self.fb.get_history_previous("")==None)
        self.assert_(self.fb.get_history_next()==None)
