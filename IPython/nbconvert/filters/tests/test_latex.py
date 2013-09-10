"""
Module with tests for Latex
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
from ..latex import escape_latex, strip_math_space, strip_url_static_file_prefix


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestLatex(TestsBase):


    def test_escape_latex(self):
        """escape_latex test"""
        tests = [
            (r'How are \you doing today?', r'How are \textbackslash{}you doing today?'),
            (r'\escapechar=`\A\catcode`\|=0 |string|foo', r'\textbackslash{}escapechar=`\textbackslash{}A\textbackslash{}catcode`\textbackslash{}|=0 |string|foo'),
            (r'# $ % & ~ _ ^ \ { }', r'\# \$ \% \& \textasciitilde{} \_ \^{} \textbackslash{} \{ \}'),
            ('...', r'\ldots'),
            ('','')]

        for test in tests:
            yield self._try_escape_latex(test[0], test[1])


    def _try_escape_latex(self, test, result):
        """Try to remove latex from string"""
        self.assertEqual(escape_latex(test), result)


    def test_strip_math_space(self):
        """strip_math_space test"""
        tests = [
            ('$e$','$e$'),
            ('$ e $','$e$'),
            ('xxx$e^i$yyy','xxx$e^i$yyy'),
            ('xxx$ e^i $yyy','xxx$e^i$yyy'),
            ('xxx$e^i $yyy','xxx$e^i$yyy'),
            ('xxx$ e^i$yyy','xxx$e^i$yyy'),
            ('\$ e $ e $','\$ e $e$'),
            ('','')]

        for test in tests:
            yield self._try_strip_math_space(test[0], test[1])


    def _try_strip_math_space(self, test, result):
        """
        Try to remove spaces between dollar symbols and contents correctly
        """
        self.assertEqual(strip_math_space(test), result)
        
        
    def test_strip_url_static_file_prefix(self):
        tests = [
            ('hello!', 'hello!'),
            ('hello![caption]', 'hello![caption]'),
            ('hello![caption](/url/location.gif)', 'hello![caption](/url/location.gif)'),
            ('hello![caption](url/location.gif)', 'hello![caption](url/location.gif)'),
            ('hello![caption](url/location.gif)', 'hello![caption](url/location.gif)'),
            ('hello![caption](files/url/location.gif)', 'hello![caption](url/location.gif)'),
            ('hello![caption](/files/url/location.gif)', 'hello![caption](url/location.gif)'),
        ]
        
        for test in tests:
            yield self._test_strip_url_static_file_prefix(test[0], test[1])

    def _test_strip_url_static_file_prefix(self, test, result):
        self.assertEqual(strip_url_static_file_prefix(test), result)
        
