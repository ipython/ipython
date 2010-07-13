# Standard library imports
import unittest

# System library imports
from pygments.lexers import CLexer, CppLexer, PythonLexer

# Local imports
from IPython.frontend.qt.console.completion_lexer import CompletionLexer


class TestCompletionLexer(unittest.TestCase):
    
    def testPython(self):
        """ Does the CompletionLexer work for Python?
        """
        lexer = CompletionLexer(PythonLexer())

        self.assertEquals(lexer.get_context("foo.bar.baz"),
                          [ "foo", "bar", "baz" ])
        self.assertEquals(lexer.get_context("foo.bar."), [ "foo", "bar", "" ])

        self.assertEquals(lexer.get_context(">>> foo.bar.baz"),
                          [ "foo", "bar", "baz" ])
        self.assertEquals(lexer.get_context("foo.bar. baz"), [ "baz" ])

    def testC(self):
        """ Does the CompletionLexer work for C/C++?
        """
        lexer = CompletionLexer(CLexer())
        self.assertEquals(lexer.get_context("foo.bar"), [ "foo", "bar" ])
        self.assertEquals(lexer.get_context("foo->bar"), [ "foo", "bar" ])

        lexer = CompletionLexer(CppLexer())
        self.assertEquals(lexer.get_context("Foo::Bar"), [ "Foo", "Bar" ])


if __name__ == '__main__':
    unittest.main()
