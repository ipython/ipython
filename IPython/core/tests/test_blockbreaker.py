"""Tests for the blockbreaker module.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import unittest

# Third party
import nose.tools as nt

# Our own
from IPython.core import blockbreaker as BB

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
def test_spaces():
    tests = [('', 0),
             (' ', 1),
             ('\n', 0),
             (' \n', 1),
             ('x', 0),
             (' x', 1),
             ('  x',2),
             ('    x',4),
             # Note: tabs are counted as a single whitespace!
             ('\tx', 1),
             ('\t x', 2),
             ]
    
    for s, nsp in tests:
        nt.assert_equal(BB.num_ini_spaces(s), nsp)


def test_remove_comments():
    tests = [('text', 'text'),
             ('text # comment', 'text '),
             ('text # comment\n', 'text \n'),
             ('text # comment \n', 'text \n'),
             ('line # c \nline\n','line \nline\n'),
             ('line # c \nline#c2  \nline\nline #c\n\n',
              'line \nline\nline\nline \n\n'),
             ]

    for inp, out in tests:
        nt.assert_equal(BB.remove_comments(inp), out)


def test_get_input_encoding():
    encoding = BB.get_input_encoding()
    nt.assert_true(isinstance(encoding, basestring))
    # simple-minded check that at least encoding a simple string works with the
    # encoding we got.
    nt.assert_equal('test'.encode(encoding), 'test')


class BlockBreakerTestCase(unittest.TestCase):
    def setUp(self):
        self.bb = BB.BlockBreaker()

    def test_reset(self):
        bb = self.bb
        bb.push('x=1')
        bb.reset()
        self.assertEqual(bb._buffer, [])
        self.assertEqual(bb.indent_spaces, 0)
        self.assertEqual(bb.get_source(), '')
        self.assertEqual(bb.code, None)

    def test_source(self):
        self.bb._store('1')
        self.bb._store('2')
        out = self.bb.get_source()
        self.assertEqual(out, '1\n2\n')
        out = self.bb.get_source(reset=True)
        self.assertEqual(out, '1\n2\n')
        self.assertEqual(self.bb._buffer, [])
        out = self.bb.get_source()
        self.assertEqual(out, '')
        
    def test_indent(self):
        bb = self.bb # shorthand
        bb.push('x=1')
        self.assertEqual(bb.indent_spaces, 0)
        bb.push('if 1:\n    x=1')
        self.assertEqual(bb.indent_spaces, 4)
        bb.push('y=2\n')
        self.assertEqual(bb.indent_spaces, 0)
        bb.push('if 1:')
        self.assertEqual(bb.indent_spaces, 4)
        bb.push('    x=1')
        self.assertEqual(bb.indent_spaces, 4)
        # Blank lines shouldn't change the indent level
        bb.push(' '*2)
        self.assertEqual(bb.indent_spaces, 4)

    def test_indent2(self):
        bb = self.bb
        # When a multiline statement contains parens or multiline strings, we
        # shouldn't get confused.
        bb.push("if 1:")
        bb.push("    x = (1+\n    2)")
        self.assertEqual(bb.indent_spaces, 4)

    def test_dedent(self):
        bb = self.bb # shorthand
        bb.push('if 1:')
        self.assertEqual(bb.indent_spaces, 4)
        bb.push('    pass')
        self.assertEqual(bb.indent_spaces, 0)
        
    def test_push(self):
        bb = self.bb
        bb.push('x=1')
        self.assertTrue(bb.is_complete)

    def test_push2(self):
        bb = self.bb
        bb.push('if 1:')
        self.assertFalse(bb.is_complete)
        for line in ['  x=1', '# a comment', '  y=2']:
            bb.push(line)
            self.assertTrue(bb.is_complete)
            
    def test_push3(self):
        """Test input with leading whitespace"""
        bb = self.bb
        bb.push('  x=1')
        bb.push('  y=2')
        self.assertEqual(bb.source, 'if 1:\n  x=1\n  y=2\n')

    def test_replace_mode(self):
        bb = self.bb
        bb.input_mode = 'replace'
        bb.push('x=1')
        self.assertEqual(bb.source, 'x=1\n')
        bb.push('x=2')
        self.assertEqual(bb.source, 'x=2\n')

    def test_interactive_block_ready(self):
        bb = self.bb
        bb.push('x=1')
        self.assertTrue(bb.interactive_block_ready())

    def test_interactive_block_ready2(self):
        bb = self.bb
        bb.push('if 1:')
        self.assertFalse(bb.interactive_block_ready())
        bb.push('  x=1')
        self.assertFalse(bb.interactive_block_ready())
        bb.push('')
        self.assertTrue(bb.interactive_block_ready())
        
    def test_interactive_block_ready3(self):
        bb = self.bb
        bb.push("x = (2+\n3)")
        self.assertTrue(bb.interactive_block_ready())

    def test_interactive_block_ready4(self):
        bb = self.bb
        # When a multiline statement contains parens or multiline strings, we
        # shouldn't get confused.
        # FIXME: we should be able to better handle de-dents in statements like
        # multiline strings and multiline expressions (continued with \ or
        # parens).  Right now we aren't handling the indentation tracking quite
        # correctly with this, though in practice it may not be too much of a
        # problem.  We'll need to see.
        bb.push("if 1:")
        bb.push("    x = (2+")
        bb.push("    3)")
        self.assertFalse(bb.interactive_block_ready())
        bb.push("    y = 3")
        self.assertFalse(bb.interactive_block_ready())
        bb.push('')
        self.assertTrue(bb.interactive_block_ready())
