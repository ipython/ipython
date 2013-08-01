"""
Module with tests for Highlight
"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from ...tests.base import TestsBase
from ..highlight import highlight2html, highlight2latex


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestHighlight(TestsBase):
    """Contains test functions for highlight.py"""

    #Hello world test, magics test, blank string test
    tests = [
        """
        #Hello World Example

        def say(text):
            print(text)

        say('Hello World!')
        """,
        """
        %%pylab
        plot(x,y, 'r')
        """
        ]   

    tokens = [
        ['Hello World Example', 'say', 'text', 'print', 'def'],
        ['pylab', 'plot']]


    def test_highlight2html(self):
        """highlight2html test"""
        for index, test in enumerate(self.tests):
            yield self._try_highlight(highlight2html, test, self.tokens[index])


    def test_highlight2latex(self):
        """highlight2latex test"""
        for index, test in enumerate(self.tests):
            yield self._try_highlight(highlight2latex, test, self.tokens[index])


    def _try_highlight(self, method, test, tokens):
        """Try highlighting source, look for key tokens"""
        results = method(test)
        for token in tokens:
            assert token in results
