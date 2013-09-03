
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

from copy import copy

from IPython.utils.py3compat import string_types
from IPython.testing import decorators as dec

from ...tests.base import TestsBase
from ..markdown import markdown2latex, markdown2html, markdown2rst


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

    tokens = [
        '*test',
        '**test',
        'test',
        'test',
        'test',
        'test',
        'test',
        'test',
        'test',
        'test',
        ('test', 'https://google.com/')]


    @dec.onlyif_cmds_exist('pandoc')
    def test_markdown2latex(self):
        """markdown2latex test"""
        for index, test in enumerate(self.tests):
            self._try_markdown(markdown2latex, test, self.tokens[index])


    @dec.onlyif_cmds_exist('pandoc')
    def test_markdown2html(self):
        """markdown2html test"""
        for index, test in enumerate(self.tests):
            self._try_markdown(markdown2html, test, self.tokens[index])


    @dec.onlyif_cmds_exist('pandoc')
    def test_markdown2rst(self):
        """markdown2rst test"""

        #Modify token array for rst, escape asterik
        tokens = copy(self.tokens)
        tokens[0] = r'\*test'
        tokens[1] = r'\*\*test'

        for index, test in enumerate(self.tests):
            self._try_markdown(markdown2rst, test, tokens[index])


    def _try_markdown(self, method, test, tokens):
        results = method(test)
        if isinstance(tokens, string_types):
            assert tokens in results
        else:
            for token in tokens:
                assert token in results
