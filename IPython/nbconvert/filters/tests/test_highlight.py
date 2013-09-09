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
from ..highlight import highlight2html, highlight2latex, which_magic_language


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
            self._try_highlight(highlight2html, test, self.tokens[index])

    def test_highlight2latex(self):
        """highlight2latex test"""
        for index, test in enumerate(self.tests):
            self._try_highlight(highlight2latex, test, self.tokens[index])

    def _try_highlight(self, method, test, tokens):
        """Try highlighting source, look for key tokens"""
        results = method(test)
        for token in tokens:
            assert token in results

    magic_tests = {
            'r':
                """%%R -i x,y -o XYcoef
                lm.fit <- lm(y~x)
                par(mfrow=c(2,2))
                print(summary(lm.fit))
                plot(lm.fit)
                XYcoef <- coef(lm.fit)
                """,
            'bash':
                """# the following code is in bash
                %%bash
                echo "test" > out
                """,
            'ipython':
                """# this should not be detected
                print("%%R")
                """
            }

    def test_highlight_rmagic(self):
        """Test %%R magic highlighting"""
        language = which_magic_language(self.magic_tests['r'])
        assert language == 'r'

    def test_highlight_bashmagic(self):
        """Test %%bash magic highlighting"""
        language = which_magic_language(self.magic_tests['bash'])
        assert language == 'bash'

    def test_highlight_interferemagic(self):
        """Test that magic highlighting does not interfere with ipython code"""
        language = which_magic_language(self.magic_tests['ipython'])
        assert language == None