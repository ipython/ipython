# coding: utf-8
"""Tests for conversions from markdown to other formats"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import re
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
        'test [link](https://google.com/)',
    ]

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
        ('test', 'https://google.com/'),
    ]


    @dec.onlyif_cmds_exist('pandoc')
    def test_markdown2latex(self):
        """markdown2latex test"""
        for index, test in enumerate(self.tests):
            self._try_markdown(markdown2latex, test, self.tokens[index])

    @dec.onlyif_cmds_exist('pandoc')
    def test_markdown2latex_markup(self):
        """markdown2latex with markup kwarg test"""
        # This string should be passed through unaltered with pandoc's
        # markdown_strict reader
        s = '1) arabic number with parenthesis'
        self.assertEqual(markdown2latex(s, markup='markdown_strict'), s)
        # This string should be passed through unaltered with pandoc's
        # markdown_strict+tex_math_dollars reader
        s = r'$\alpha$ latex math'
        # sometimes pandoc uses $math$, sometimes it uses \(math\)
        expected = re.compile(r'(\$|\\\()\\alpha(\$|\\\)) latex math')
        try:
            # py3
            assertRegex = self.assertRegex
        except AttributeError:
            # py2
            assertRegex = self.assertRegexpMatches
        assertRegex(
            markdown2latex(s, markup='markdown_strict+tex_math_dollars'),
            expected)

    @dec.onlyif_cmds_exist('pandoc')
    def test_pandoc_extra_args(self):
        # pass --no-wrap
        s = '\n'.join([
            "#latex {{long_line | md2l('markdown', ['--no-wrap'])}}",
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

    def test_markdown2html_heading_anchors(self):
        for md, tokens in [
            ('# test',
                ('<h1', '>test', 'id="test"', u'&#182;</a>', "anchor-link")
            ),
            ('###test head space',
                ('<h3', '>test head space', 'id="test-head-space"', u'&#182;</a>', "anchor-link")
            )
        ]:
            self._try_markdown(markdown2html, md, tokens)

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
    
    def test_markdown2html_math_mixed(self):
        """ensure markdown between inline and inline-block math"""
        case = """The entries of $C$ are given by the exact formula:
$$
C_{ik} = \sum_{j=1}^n A_{ij} B_{jk}
$$
but there are many ways to _implement_ this computation.   $\approx 2mnp$ flops"""
        self._try_markdown(markdown2html, case,
                           case.replace("_implement_", "<em>implement</em>"))

    def test_markdown2html_math_paragraph(self):
        """these should all parse without modification"""
        cases = [
            # https://github.com/ipython/ipython/issues/6724
            """Water that is stored in $t$, $s_t$, must equal the storage content of the previous stage,
$s_{t-1}$, plus a stochastic inflow, $I_t$, minus what is being released in $t$, $r_t$.
With $s_0$ defined as the initial storage content in $t=1$, we have""",
            # https://github.com/jupyter/nbviewer/issues/420
            """$C_{ik}$
$$
C_{ik} = \sum_{j=1}
$$
$C_{ik}$""",
            """$m$
$$
C = \begin{pmatrix}
          0 & 0 & 0 & \cdots & 0 & 0 & -c_0 \\
          0 & 0 & 0 & \cdots & 0 & 1 & -c_{m-1}
    \end{pmatrix}
$$
$x^m$""",
            """$r=\overline{1,n}$
$$ {\bf
b}_{i}^{r}(t)=(1-t)\,{\bf b}_{i}^{r-1}(t)+t\,{\bf b}_{i+1}^{r-1}(t),\:
 i=\overline{0,n-r}, $$
i.e. the $i^{th}$"""
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
