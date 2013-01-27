# -*- coding: utf-8 -*-
"""Tests for the inputsplitter module.

Authors
-------
* Fernando Perez
* Robert Kern
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import unittest
import sys

# Third party
import nose.tools as nt

# Our own
from IPython.core import inputsplitter as isp
from IPython.core.tests.test_inputtransformer import syntax, syntax_ml
from IPython.testing import tools as tt
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Semi-complete examples (also used as tests)
#-----------------------------------------------------------------------------

# Note: at the bottom, there's a slightly more complete version of this that
# can be useful during development of code here.

def mini_interactive_loop(input_func):
    """Minimal example of the logic of an interactive interpreter loop.

    This serves as an example, and it is used by the test system with a fake
    raw_input that simulates interactive input."""

    from IPython.core.inputsplitter import InputSplitter

    isp = InputSplitter()
    # In practice, this input loop would be wrapped in an outside loop to read
    # input indefinitely, until some exit/quit command was issued.  Here we
    # only illustrate the basic inner loop.
    while isp.push_accepts_more():
        indent = ' '*isp.indent_spaces
        prompt = '>>> ' + indent
        line = indent + input_func(prompt)
        isp.push(line)

    # Here we just return input so we can use it in a test suite, but a real
    # interpreter would instead send it for execution somewhere.
    src = isp.source_reset()
    #print 'Input source was:\n', src  # dbg
    return src

#-----------------------------------------------------------------------------
# Test utilities, just for local use
#-----------------------------------------------------------------------------

def assemble(block):
    """Assemble a block into multi-line sub-blocks."""
    return ['\n'.join(sub_block)+'\n' for sub_block in block]


def pseudo_input(lines):
    """Return a function that acts like raw_input but feeds the input list."""
    ilines = iter(lines)
    def raw_in(prompt):
        try:
            return next(ilines)
        except StopIteration:
            return ''
    return raw_in

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
    tt.check_pairs(isp.num_ini_spaces, tests)


def test_remove_comments():
    tests = [('text', 'text'),
             ('text # comment', 'text '),
             ('text # comment\n', 'text \n'),
             ('text # comment \n', 'text \n'),
             ('line # c \nline\n','line \nline\n'),
             ('line # c \nline#c2  \nline\nline #c\n\n',
              'line \nline\nline\nline \n\n'),
             ]
    tt.check_pairs(isp.remove_comments, tests)


def test_get_input_encoding():
    encoding = isp.get_input_encoding()
    nt.assert_true(isinstance(encoding, basestring))
    # simple-minded check that at least encoding a simple string works with the
    # encoding we got.
    nt.assert_equal(u'test'.encode(encoding), b'test')


class NoInputEncodingTestCase(unittest.TestCase):
    def setUp(self):
        self.old_stdin = sys.stdin
        class X: pass
        fake_stdin = X()
        sys.stdin = fake_stdin

    def test(self):
        # Verify that if sys.stdin has no 'encoding' attribute we do the right
        # thing
        enc = isp.get_input_encoding()
        self.assertEqual(enc, 'ascii')

    def tearDown(self):
        sys.stdin = self.old_stdin


class InputSplitterTestCase(unittest.TestCase):
    def setUp(self):
        self.isp = isp.InputSplitter()

    def test_reset(self):
        isp = self.isp
        isp.push('x=1')
        isp.reset()
        self.assertEqual(isp._buffer, [])
        self.assertEqual(isp.indent_spaces, 0)
        self.assertEqual(isp.source, '')
        self.assertEqual(isp.code, None)
        self.assertEqual(isp._is_complete, False)

    def test_source(self):
        self.isp._store('1')
        self.isp._store('2')
        self.assertEqual(self.isp.source, '1\n2\n')
        self.assertTrue(len(self.isp._buffer)>0)
        self.assertEqual(self.isp.source_reset(), '1\n2\n')
        self.assertEqual(self.isp._buffer, [])
        self.assertEqual(self.isp.source, '')

    def test_indent(self):
        isp = self.isp # shorthand
        isp.push('x=1')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n    x=1')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('y=2\n')
        self.assertEqual(isp.indent_spaces, 0)

    def test_indent2(self):
        # In cell mode, inputs must be fed in whole blocks, so skip this test
        if self.isp.input_mode == 'cell': return

        isp = self.isp
        isp.push('if 1:')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('    x=1')
        self.assertEqual(isp.indent_spaces, 4)
        # Blank lines shouldn't change the indent level
        isp.push(' '*2)
        self.assertEqual(isp.indent_spaces, 4)

    def test_indent3(self):
        # In cell mode, inputs must be fed in whole blocks, so skip this test
        if self.isp.input_mode == 'cell': return

        isp = self.isp
        # When a multiline statement contains parens or multiline strings, we
        # shouldn't get confused.
        isp.push("if 1:")
        isp.push("    x = (1+\n    2)")
        self.assertEqual(isp.indent_spaces, 4)

    def test_indent4(self):
        # In cell mode, inputs must be fed in whole blocks, so skip this test
        if self.isp.input_mode == 'cell': return

        isp = self.isp
        # whitespace after ':' should not screw up indent level
        isp.push('if 1: \n    x=1')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('y=2\n')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\t\n    x=1')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('y=2\n')
        self.assertEqual(isp.indent_spaces, 0)

    def test_dedent_pass(self):
        isp = self.isp # shorthand
        # should NOT cause dedent
        isp.push('if 1:\n    passes = 5')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('if 1:\n     pass')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n     pass   ')
        self.assertEqual(isp.indent_spaces, 0)

    def test_dedent_break(self):
        isp = self.isp # shorthand
        # should NOT cause dedent
        isp.push('while 1:\n    breaks = 5')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('while 1:\n     break')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('while 1:\n     break   ')
        self.assertEqual(isp.indent_spaces, 0)

    def test_dedent_continue(self):
        isp = self.isp # shorthand
        # should NOT cause dedent
        isp.push('while 1:\n    continues = 5')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('while 1:\n     continue')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('while 1:\n     continue   ')
        self.assertEqual(isp.indent_spaces, 0)

    def test_dedent_raise(self):
        isp = self.isp # shorthand
        # should NOT cause dedent
        isp.push('if 1:\n    raised = 4')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('if 1:\n     raise TypeError()')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n     raise')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n     raise      ')
        self.assertEqual(isp.indent_spaces, 0)

    def test_dedent_return(self):
        isp = self.isp # shorthand
        # should NOT cause dedent
        isp.push('if 1:\n    returning = 4')
        self.assertEqual(isp.indent_spaces, 4)
        isp.push('if 1:\n     return 5 + 493')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n     return')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n     return      ')
        self.assertEqual(isp.indent_spaces, 0)
        isp.push('if 1:\n     return(0)')
        self.assertEqual(isp.indent_spaces, 0)

    def test_push(self):
        isp = self.isp
        self.assertTrue(isp.push('x=1'))

    def test_push2(self):
        isp = self.isp
        self.assertFalse(isp.push('if 1:'))
        for line in ['  x=1', '# a comment', '  y=2']:
            print(line)
            self.assertTrue(isp.push(line))

    def test_push3(self):
        isp = self.isp
        isp.push('if True:')
        isp.push('  a = 1')
        self.assertFalse(isp.push('b = [1,'))

    def test_replace_mode(self):
        isp = self.isp
        isp.input_mode = 'cell'
        isp.push('x=1')
        self.assertEqual(isp.source, 'x=1\n')
        isp.push('x=2')
        self.assertEqual(isp.source, 'x=2\n')

    def test_push_accepts_more(self):
        isp = self.isp
        isp.push('x=1')
        self.assertFalse(isp.push_accepts_more())

    def test_push_accepts_more2(self):
        # In cell mode, inputs must be fed in whole blocks, so skip this test
        if self.isp.input_mode == 'cell': return

        isp = self.isp
        isp.push('if 1:')
        self.assertTrue(isp.push_accepts_more())
        isp.push('  x=1')
        self.assertTrue(isp.push_accepts_more())
        isp.push('')
        self.assertFalse(isp.push_accepts_more())

    def test_push_accepts_more3(self):
        isp = self.isp
        isp.push("x = (2+\n3)")
        self.assertFalse(isp.push_accepts_more())

    def test_push_accepts_more4(self):
        # In cell mode, inputs must be fed in whole blocks, so skip this test
        if self.isp.input_mode == 'cell': return

        isp = self.isp
        # When a multiline statement contains parens or multiline strings, we
        # shouldn't get confused.
        # FIXME: we should be able to better handle de-dents in statements like
        # multiline strings and multiline expressions (continued with \ or
        # parens).  Right now we aren't handling the indentation tracking quite
        # correctly with this, though in practice it may not be too much of a
        # problem.  We'll need to see.
        isp.push("if 1:")
        isp.push("    x = (2+")
        isp.push("    3)")
        self.assertTrue(isp.push_accepts_more())
        isp.push("    y = 3")
        self.assertTrue(isp.push_accepts_more())
        isp.push('')
        self.assertFalse(isp.push_accepts_more())

    def test_push_accepts_more5(self):
        # In cell mode, inputs must be fed in whole blocks, so skip this test
        if self.isp.input_mode == 'cell': return

        isp = self.isp
        isp.push('try:')
        isp.push('    a = 5')
        isp.push('except:')
        isp.push('    raise')
        self.assertTrue(isp.push_accepts_more())

    def test_continuation(self):
        isp = self.isp
        isp.push("import os, \\")
        self.assertTrue(isp.push_accepts_more())
        isp.push("sys")
        self.assertFalse(isp.push_accepts_more())

    def test_syntax_error(self):
        isp = self.isp
        # Syntax errors immediately produce a 'ready' block, so the invalid
        # Python can be sent to the kernel for evaluation with possible ipython
        # special-syntax conversion.
        isp.push('run foo')
        self.assertFalse(isp.push_accepts_more())

    def test_unicode(self):
        self.isp.push(u"Pérez")
        self.isp.push(u'\xc3\xa9')
        self.isp.push(u"u'\xc3\xa9'")

    def test_line_continuation(self):
        """ Test issue #2108."""
        isp = self.isp
        # A blank line after a line continuation should not accept more
        isp.push("1 \\\n\n")
        self.assertFalse(isp.push_accepts_more())
        # Whitespace after a \ is a SyntaxError.  The only way to test that
        # here is to test that push doesn't accept more (as with
        # test_syntax_error() above).
        isp.push(r"1 \ ")
        self.assertFalse(isp.push_accepts_more())
        # Even if the line is continuable (c.f. the regular Python
        # interpreter)
        isp.push(r"(1 \ ")
        self.assertFalse(isp.push_accepts_more())

class InteractiveLoopTestCase(unittest.TestCase):
    """Tests for an interactive loop like a python shell.
    """
    def check_ns(self, lines, ns):
        """Validate that the given input lines produce the resulting namespace.

        Note: the input lines are given exactly as they would be typed in an
        auto-indenting environment, as mini_interactive_loop above already does
        auto-indenting and prepends spaces to the input.
        """
        src = mini_interactive_loop(pseudo_input(lines))
        test_ns = {}
        exec src in test_ns
        # We can't check that the provided ns is identical to the test_ns,
        # because Python fills test_ns with extra keys (copyright, etc).  But
        # we can check that the given dict is *contained* in test_ns
        for k,v in ns.iteritems():
            self.assertEqual(test_ns[k], v)

    def test_simple(self):
        self.check_ns(['x=1'], dict(x=1))

    def test_simple2(self):
        self.check_ns(['if 1:', 'x=2'], dict(x=2))

    def test_xy(self):
        self.check_ns(['x=1; y=2'], dict(x=1, y=2))

    def test_abc(self):
        self.check_ns(['if 1:','a=1','b=2','c=3'], dict(a=1, b=2, c=3))

    def test_multi(self):
        self.check_ns(['x =(1+','1+','2)'], dict(x=4))


def test_LineInfo():
    """Simple test for LineInfo construction and str()"""
    linfo = isp.LineInfo('  %cd /home')
    nt.assert_equal(str(linfo), 'LineInfo [  |%|cd|/home]')




class IPythonInputTestCase(InputSplitterTestCase):
    """By just creating a new class whose .isp is a different instance, we
    re-run the same test battery on the new input splitter.

    In addition, this runs the tests over the syntax and syntax_ml dicts that
    were tested by individual functions, as part of the OO interface.

    It also makes some checks on the raw buffer storage.
    """

    def setUp(self):
        self.isp = isp.IPythonInputSplitter(input_mode='line')

    def test_syntax(self):
        """Call all single-line syntax tests from the main object"""
        isp = self.isp
        for example in syntax.itervalues():
            for raw, out_t in example:
                if raw.startswith(' '):
                    continue

                isp.push(raw+'\n')
                out, out_raw = isp.source_raw_reset()
                self.assertEqual(out.rstrip(), out_t,
                        tt.pair_fail_msg.format("inputsplitter",raw, out_t, out))
                self.assertEqual(out_raw.rstrip(), raw.rstrip())

    def test_syntax_multiline(self):
        isp = self.isp
        for example in syntax_ml.itervalues():
            for line_pairs in example:
                out_t_parts = []
                raw_parts = []
                for lraw, out_t_part in line_pairs:
                    if out_t_part is not None:
                        out_t_parts.append(out_t_part)
                    
                    if lraw is not None:
                        isp.push(lraw)
                        raw_parts.append(lraw)

                out, out_raw = isp.source_raw_reset()
                out_t = '\n'.join(out_t_parts).rstrip()
                raw = '\n'.join(raw_parts).rstrip()
                self.assertEqual(out.rstrip(), out_t)
                self.assertEqual(out_raw.rstrip(), raw)


class BlockIPythonInputTestCase(IPythonInputTestCase):

    # Deactivate tests that don't make sense for the block mode
    test_push3 = test_split = lambda s: None

    def setUp(self):
        self.isp = isp.IPythonInputSplitter(input_mode='cell')

    def test_syntax_multiline(self):
        isp = self.isp
        for example in syntax_ml.itervalues():
            raw_parts = []
            out_t_parts = []
            for line_pairs in example:
                raw_parts, out_t_parts = zip(*line_pairs)

                raw = '\n'.join(r for r in raw_parts if r is not None)
                out_t = '\n'.join(o for o in out_t_parts if o is not None)

                isp.push(raw)
                out, out_raw = isp.source_raw_reset()
                # Match ignoring trailing whitespace
                self.assertEqual(out.rstrip(), out_t.rstrip())
                self.assertEqual(out_raw.rstrip(), raw.rstrip())

    def test_syntax_multiline_cell(self):
        isp = self.isp
        for example in syntax_ml.itervalues():

            out_t_parts = []
            for line_pairs in example:
                raw = '\n'.join(r for r, _ in line_pairs if r is not None)
                out_t = '\n'.join(t for _,t in line_pairs if t is not None)
                out = isp.transform_cell(raw)
                # Match ignoring trailing whitespace
                self.assertEqual(out.rstrip(), out_t.rstrip())

#-----------------------------------------------------------------------------
# Main - use as a script, mostly for developer experiments
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    # A simple demo for interactive experimentation.  This code will not get
    # picked up by any test suite.
    from IPython.core.inputsplitter import InputSplitter, IPythonInputSplitter

    # configure here the syntax to use, prompt and whether to autoindent
    #isp, start_prompt = InputSplitter(), '>>> '
    isp, start_prompt = IPythonInputSplitter(), 'In> '

    autoindent = True
    #autoindent = False

    try:
        while True:
            prompt = start_prompt
            while isp.push_accepts_more():
                indent = ' '*isp.indent_spaces
                if autoindent:
                    line = indent + raw_input(prompt+indent)
                else:
                    line = raw_input(prompt)
                isp.push(line)
                prompt = '... '

            # Here we just return input so we can use it in a test suite, but a
            # real interpreter would instead send it for execution somewhere.
            #src = isp.source; raise EOFError # dbg
            src, raw = isp.source_raw_reset()
            print 'Input source was:\n', src
            print 'Raw source was:\n', raw
    except EOFError:
        print 'Bye'

# Tests for cell magics support

def test_last_blank():
    nt.assert_false(isp.last_blank(''))
    nt.assert_false(isp.last_blank('abc'))
    nt.assert_false(isp.last_blank('abc\n'))
    nt.assert_false(isp.last_blank('abc\na'))

    nt.assert_true(isp.last_blank('\n'))
    nt.assert_true(isp.last_blank('\n '))
    nt.assert_true(isp.last_blank('abc\n '))
    nt.assert_true(isp.last_blank('abc\n\n'))
    nt.assert_true(isp.last_blank('abc\nd\n\n'))
    nt.assert_true(isp.last_blank('abc\nd\ne\n\n'))
    nt.assert_true(isp.last_blank('abc \n \n \n\n'))


def test_last_two_blanks():
    nt.assert_false(isp.last_two_blanks(''))
    nt.assert_false(isp.last_two_blanks('abc'))
    nt.assert_false(isp.last_two_blanks('abc\n'))
    nt.assert_false(isp.last_two_blanks('abc\n\na'))
    nt.assert_false(isp.last_two_blanks('abc\n \n'))
    nt.assert_false(isp.last_two_blanks('abc\n\n'))

    nt.assert_true(isp.last_two_blanks('\n\n'))
    nt.assert_true(isp.last_two_blanks('\n\n '))
    nt.assert_true(isp.last_two_blanks('\n \n'))
    nt.assert_true(isp.last_two_blanks('abc\n\n '))
    nt.assert_true(isp.last_two_blanks('abc\n\n\n'))
    nt.assert_true(isp.last_two_blanks('abc\n\n \n'))
    nt.assert_true(isp.last_two_blanks('abc\n\n \n '))
    nt.assert_true(isp.last_two_blanks('abc\n\n \n \n'))
    nt.assert_true(isp.last_two_blanks('abc\nd\n\n\n'))
    nt.assert_true(isp.last_two_blanks('abc\nd\ne\nf\n\n\n'))


class CellMagicsCommon(object):

    def test_whole_cell(self):
        src = "%%cellm line\nbody\n"
        sp = self.sp
        sp.push(src)
        out = sp.source_reset()
        ref = u"get_ipython().run_cell_magic({u}'cellm', {u}'line', {u}'body')\n"
        nt.assert_equal(out, py3compat.u_format(ref))

    def tearDown(self):
        self.sp.reset()


class CellModeCellMagics(CellMagicsCommon, unittest.TestCase):
    sp = isp.IPythonInputSplitter(input_mode='cell')

    def test_incremental(self):
        sp = self.sp
        src = '%%cellm line2\n'
        sp.push(src)
        nt.assert_true(sp.push_accepts_more()) #1
        src += '\n'
        sp.push(src)
        # Note: if we ever change the logic to allow full blank lines (see
        # _handle_cell_magic), then the following test should change to true
        nt.assert_false(sp.push_accepts_more()) #2
        # By now, even with full blanks allowed, a second blank should signal
        # the end.  For now this test is only a redundancy safety, but don't
        # delete it in case we change our mind and the previous one goes to
        # true.
        src += '\n'
        sp.push(src)
        nt.assert_false(sp.push_accepts_more()) #3


class LineModeCellMagics(CellMagicsCommon, unittest.TestCase):
    sp = isp.IPythonInputSplitter(input_mode='line')

    def test_incremental(self):
        sp = self.sp
        sp.push('%%cellm line2\n')
        nt.assert_true(sp.push_accepts_more()) #1
        sp.push('\n')
        nt.assert_false(sp.push_accepts_more()) #2
