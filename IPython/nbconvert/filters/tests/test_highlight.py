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
from ..highlight import *


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
    """, ""
    ]


    def test_highlight2html(self):
        """
        highlight2html test
        """
        known_results = [
        """
            <div class="highlight"><pre><span class="c">#Hello World Example</span>
            <span class="k">def</span><span class="nf">say</span><span class="p">(</span><span class="n">text</span><span class="p">):</span>
            <span class="k">print</span><span class="p">(</span><span class="n">text</span><span class="p">)</span>
            <span class="n">say</span><span class="p">(</span><span class="s">&#39;Hello World!&#39;</span><span class="p">)</span></pre></div>
        """,
        """        
            <div class="highlight"><pre><span class="o">%%</span><span class="k">pylab</span>
            <span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span><span class="n">y</span><span class="p">,</span> <span class="s">&#39;r&#39;</span><span class="p">)</span></pre></div>
        """, 
        "<div class=\"highlight\"><pre></pre></div>"]
        for index, test in enumerate(self.tests):
            yield self._try_highlight2html, test.strip(), known_results[index].strip()


    def _try_highlight2html(self, test, results):
        """
        Try highlighting source as html
        """
        assert self.fuzzy_compare(results, highlight2html(test), ignore_newlines=True, ignore_spaces=True)


    def test_highlight2latex(self):
        """
        highlight2latex test
        """
        known_results = [
        r"""
            \begin{Verbatim}[commandchars=\\\{\}]
            \PY{c}{\PYZsh{}Hello World Example}

            \PY{k}{def} \PY{n+nf}{say}\PY{p}{(}\PY{n}{text}\PY{p}{)}\PY{p}{:}
            \PY{k}{print}\PY{p}{(}\PY{n}{text}\PY{p}{)}

            \PY{n}{say}\PY{p}{(}\PY{l+s}{'}\PY{l+s}{Hello World!}\PY{l+s}{'}\PY{p}{)}
            \end{Verbatim}
        """,
        r"""        
            \begin{Verbatim}[commandchars=\\\{\}]
            \PY{o}{\PYZpc{}\PYZpc{}}\PY{k}{pylab}
            \PY{n}{plot}\PY{p}{(}\PY{n}{x}\PY{p}{,}\PY{n}{y}\PY{p}{,} \PY{l+s}{'}\PY{l+s}{r}\PY{l+s}{'}\PY{p}{)}
            \end{Verbatim}
        """, 
        r"\begin{Verbatim}[commandchars=\\\{\}]\end{Verbatim}"]
        for index, test in enumerate(self.tests):
            yield self._try_highlight2latex, test.strip(), known_results[index].strip()


    def _try_highlight2latex(self, test, results):
        """
        Try highlighting source as latex
        """
        assert self.fuzzy_compare(results, highlight2latex(test), ignore_newlines=True, ignore_spaces=True)
