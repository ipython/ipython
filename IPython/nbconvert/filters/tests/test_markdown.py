
"""
Module with tests for Markdown
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


from IPython.testing.decorators import onlyif_cmds_exist
# @onlyif_cmds_exist('pandoc')

from ...tests.base import TestsBase
from ..markdown import *


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestMarkdown(TestsBase):

    tests = [
        '*test',
        '**test',
        '*test*',
        '_test_',
        '__test__',
        '__*test*__',
        '**test**',
        '#test',
        '##test',
        'test\n----',
        'test [link](https://google.com/)',
        """
List
----
- Test
- Test
    1. Test
    2. Test
        - Test
        - Test
    2. Test
        """,
        "test\ntest",
        "test\n  test",
        "test\n\n---\n\ntest",
        "test\n\n***\n\ntest",
        """
#Code

Below

    def hello_world(self):
        print('hello_world')

        """,
        """
Quote
-----

Mike said

> You are so cool!
> I wish I could do that.
        """,
        "inline `quote`"]


    @onlyif_cmds_exist('pandoc')
    def test_markdown2latex(self):
        """
        markdown2latex test
        """
        results = [
            '*test',
            '**test',
            r'\emph{test}',
            r'\emph{test}',
            r'\textbf{test}',
            r'\textbf{\emph{test}}',
            r'\textbf{test}',
            r'\section{test}',
            r'\subsection{test}',
            r'\subsection{test}',
            r'test \href{https://google.com/}{link}',
            r"""
\subsection{List}

\begin{itemize}
\item
  Test
\item
  Test

  \begin{enumerate}[1.]
  \item
    Test
  \item
    Test

    \begin{itemize}
    \item
      Test
    \item
      Test
    \end{itemize}
  \item
    Test
  \end{enumerate}
\end{itemize}
            """,
            'test test',
            'test test',
            r"""
            test

            \begin{center}\rule{3in}{0.4pt}\end{center}

            test
            """,
            r"""
            test

            \begin{center}\rule{3in}{0.4pt}\end{center}

            test
            """,
            r"""
\section{Code}

Below

\begin{verbatim}
def hello_world(self):
    print('hello_world')
\end{verbatim}

            """,
            r"""
\subsection{Quote}

Mike said

\begin{quote}
You are so cool! I wish I could do that.
\end{quote}
            """,
            r'inline \texttt{quote}']   
        for index, test in enumerate(self.tests):
            yield self._try_markdown2latex, test, results[index]


    def _try_markdown2latex(self, test, results):
        assert self.fuzzy_compare(markdown2latex(test), results)


    @onlyif_cmds_exist('pandoc')
    def test_markdown2html(self):
        """
        markdown2html test
        """
        results = [
            '<p>*test</p>',
            '<p>**test</p>',
            '<p><em>test</em></p>',
            '<p><em>test</em></p>',
            '<p><strong>test</strong></p>',
            '<p><strong><em>test</em></strong></p>',
            '<p><strong>test</strong></p>',
            '<h1 id="test">test</h1>',
            '<h2 id="test">test</h2>',
            '<h2 id="test">test</h2>',
            '<p>test <a href="https://google.com/">link</a></p>',
            """
<h2 id="list">List</h2>
<ul>
<li>Test</li>
<li>Test
<ol style="list-style-type: decimal">
<li>Test</li>
<li>Test
<ul>
<li>Test</li>
<li>Test</li>
</ul></li>
<li>Test</li>
</ol></li>
</ul>

            """,
            '<p>test test</p>',
            '<p>test test</p>',
            """
            <p>test</p>
            <hr />
            <p>test</p>
            """,
            """
            <p>test</p>
            <hr />
            <p>test</p>
            """,
            """
<h1 id="code">Code</h1>
<p>Below</p>
<pre><code>def hello_world(self):
    print(&#39;hello_world&#39;)</code></pre>

            """,
            """
<h2 id="quote">Quote</h2>
<p>Mike said</p>
<blockquote>
<p>You are so cool! I wish I could do that.</p>
</blockquote>

            """,
            '<p>inline <code>quote</code></p>']   
        for index, test in enumerate(self.tests):
            yield self._try_markdown2html, test, results[index]


    def _try_markdown2html(self, test, results):
        assert self.fuzzy_compare(markdown2html(test), results)


    @onlyif_cmds_exist('pandoc')
    def test_markdown2rst(self):
        """
        markdown2rst test
        """
        results = [
            '\*test',
            '\*\*test',
            '*test*',
            '*test*',
            '**test**',
            '***test***',
            '**test**',
            'test\n====',
            'test\n----',
            'test\n----',
            'test `link <https://google.com/>`_',
            """
List
----

-  Test
-  Test

   1. Test
   2. Test

      -  Test
      -  Test

   3. Test

            """,
            'test test',
            'test test',
            """
test

--------------

test
            """,
            """
test

--------------

test

            """,
            """
Code
====

Below

::

    def hello_world(self):
        print('hello_world')

            """,
            """
Quote
-----

Mike said

    You are so cool! I wish I could do that.

            """,
            'inline ``quote``']       
        for index, test in enumerate(self.tests):
            yield self._try_markdown2rst, test, results[index]


    def _try_markdown2rst(self, test, results):
        assert self.fuzzy_compare(markdown2rst(test), results)
