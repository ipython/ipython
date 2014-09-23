"""Tests for conversions from markdown to other formats"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from copy import copy

from IPython.utils.py3compat import string_types
from IPython.testing import decorators as dec

from ...tests.base import TestsBase
from ..markdown import markdown2latex, markdown2html, markdown2rst

from jinja2 import Environment

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
    def test_pandoc_extra_args(self):
        # pass --no-wrap
        s = '\n'.join([
            "#latex {{long_line | md2l(['--no-wrap'])}}",
            "#rst {{long_line | md2r(['--columns', '5'])}}",
        ])
        long_line = ' '.join(['long'] * 30)
        env = Environment()
        env.filters.update({
            'md2l': markdown2latex,
            'md2r': markdown2rst,
        })
        tpl = env.from_string(s)
        rendered = tpl.render(long_line=long_line)
        _, latex, rst = rendered.split('#')
        
        self.assertEqual(latex.strip(), 'latex %s' % long_line)
        self.assertEqual(rst.strip(), 'rst %s' % long_line.replace(' ', '\n'))

    def test_markdown2html(self):
        """markdown2html test"""
        for index, test in enumerate(self.tests):
            self._try_markdown(markdown2html, test, self.tokens[index])

    def test_markdown2html_math(self):
        # Mathematical expressions should be passed through unaltered
        cases = [("\\begin{equation*}\n"
                  "\\left( \\sum_{k=1}^n a_k b_k \\right)^2 \\leq \\left( \\sum_{k=1}^n a_k^2 \\right) \\left( \\sum_{k=1}^n b_k^2 \\right)\n"
                  "\\end{equation*}"),
                 ("$$\n"
                  "a = 1 *3* 5\n"
                  "$$"),
                  "$ a = 1 *3* 5 $",
                ]
        for case in cases:
            self.assertIn(case, markdown2html(case))


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
