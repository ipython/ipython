
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
        'test [link](https://google.com/)']


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
            r'test \href{https://google.com/}{link}']   
        for index, test in enumerate(self.tests):
            yield self._try_markdown2latex, test, results[index]


    def _try_markdown2latex(self, test, results):
        self.fuzzy_compare(markdown2latex(test), results)


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
            '<p>test <a href="https://google.com/">link</a></p>']   
        for index, test in enumerate(self.tests):
            yield self._try_markdown2html, test, results[index]


    def _try_markdown2html(self, test, results):
        self.fuzzy_compare(markdown2html(test), results)


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
            'test `link <https://google.com/>`_']       
        for index, test in enumerate(self.tests):
            yield self._try_markdown2rst, test, results[index]


    def _try_markdown2rst(self, test, results):
        self.fuzzy_compare(markdown2rst(test), results)
