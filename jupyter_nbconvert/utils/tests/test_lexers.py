"""Test lexers module"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2014 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from pygments.token import Token

from IPython.nbconvert.tests.base import TestsBase
from .. import lexers


#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class TestLexers(TestsBase):
    """Collection of lexers tests"""
    def setUp(self):
        self.lexer = lexers.IPythonLexer()

    def testIPythonLexer(self):
        fragment = '!echo $HOME\n'
        tokens = [
            (Token.Operator, '!'),
            (Token.Name.Builtin, 'echo'),
            (Token.Text, ' '),
            (Token.Name.Variable, '$HOME'),
            (Token.Text, '\n'),
        ]
        self.assertEqual(tokens, list(self.lexer.get_tokens(fragment)))

        fragment_2 = '!' + fragment
        tokens_2 = [
            (Token.Operator, '!!'),
        ] + tokens[1:]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = '\t %%!\n' + fragment[1:]
        tokens_2 = [
            (Token.Text, '\t '),
            (Token.Operator, '%%!'),
            (Token.Text, '\n'),
        ] + tokens[1:]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = 'x = ' + fragment
        tokens_2 = [
            (Token.Name, 'x'),
            (Token.Text, ' '),
            (Token.Operator, '='),
            (Token.Text, ' '),
        ] + tokens
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = 'x, = ' + fragment
        tokens_2 = [
            (Token.Name, 'x'),
            (Token.Punctuation, ','),
            (Token.Text, ' '),
            (Token.Operator, '='),
            (Token.Text, ' '),
        ] + tokens
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = 'x, = %sx ' + fragment[1:]
        tokens_2 = [
            (Token.Name, 'x'),
            (Token.Punctuation, ','),
            (Token.Text, ' '),
            (Token.Operator, '='),
            (Token.Text, ' '),
            (Token.Operator, '%'),
            (Token.Keyword, 'sx'),
            (Token.Text, ' '),
        ] + tokens[1:]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = 'f = %R function () {}\n'
        tokens_2 = [
            (Token.Name, 'f'),
            (Token.Text, ' '),
            (Token.Operator, '='),
            (Token.Text, ' '),
            (Token.Operator, '%'),
            (Token.Keyword, 'R'),
            (Token.Text, ' function () {}\n'),
        ]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = '\t%%xyz\n$foo\n'
        tokens_2 = [
            (Token.Text, '\t'),
            (Token.Operator, '%%'),
            (Token.Keyword, 'xyz'),
            (Token.Text, '\n$foo\n'),
        ]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = '%system?\n'
        tokens_2 = [
            (Token.Operator, '%'),
            (Token.Keyword, 'system'),
            (Token.Operator, '?'),
            (Token.Text, '\n'),
        ]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = 'x != y\n'
        tokens_2 = [
            (Token.Name, 'x'),
            (Token.Text, ' '),
            (Token.Operator, '!='),
            (Token.Text, ' '),
            (Token.Name, 'y'),
            (Token.Text, '\n'),
        ]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))

        fragment_2 = ' ?math.sin\n'
        tokens_2 = [
            (Token.Text, ' '),
            (Token.Operator, '?'),
            (Token.Text, 'math.sin'),
            (Token.Text, '\n'),
        ]
        self.assertEqual(tokens_2, list(self.lexer.get_tokens(fragment_2)))
