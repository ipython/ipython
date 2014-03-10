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
from ..highlight import Highlight2HTML, Highlight2Latex
from IPython.config import Config
import xml

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

highlight2html = Highlight2HTML()
highlight2latex = Highlight2Latex()
c = Config()
c.Highlight2HTML.default_language='ruby'
highlight2html_ruby = Highlight2HTML(config=c)

class TestHighlight(TestsBase):
    """Contains test functions for highlight.py"""

    #Hello world test, magics test, blank string test
    tests = [
        """
        #Hello World Example

        def say(text):
            print(text)

        end

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

    def test_parse_html_many_lang(self):

        ht =  highlight2html(self.tests[0])
        rb =  highlight2html_ruby(self.tests[0])

        for lang,tkns in [
                ( ht, ('def','print') ),
                ( rb, ('def','end'  ) )
                ]:
            root = xml.etree.ElementTree.fromstring(lang)
            assert self._extract_tokens(root,'k') == set(tkns)

    def _extract_tokens(self, root, cls):
        return set(map(lambda x:x.text,root.findall(".//*[@class='"+cls+"']")))

    def _try_highlight(self, method, test, tokens):
        """Try highlighting source, look for key tokens"""
        results = method(test)
        for token in tokens:
            assert token in results
