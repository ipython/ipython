# -*- coding: utf-8 -*-
"""Tests for the key interactiveshell module.

Authors
-------
* Julian Taylor
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import sys
import types
import unittest

from IPython.core.inputtransformer import InputTransformer
from IPython.testing.decorators import skipif
from IPython.utils import py3compat
from IPython.testing import tools as tt

# Decorator for interaction loop tests -----------------------------------------

class mock_input_helper(object):
    """Machinery for tests of the main interact loop.

    Used by the mock_input decorator.
    """
    def __init__(self, testgen):
        self.testgen = testgen
        self.exception = None
        self.ip = get_ipython()

    def __enter__(self):
        self.orig_raw_input = self.ip.raw_input
        self.ip.raw_input = self.fake_input
        return self

    def __exit__(self, etype, value, tb):
        self.ip.raw_input = self.orig_raw_input

    def fake_input(self, prompt):
        try:
            return next(self.testgen)
        except StopIteration:
            self.ip.exit_now = True
            return u''
        except:
            self.exception = sys.exc_info()
            self.ip.exit_now = True
            return u''

def mock_input(testfunc):
    """Decorator for tests of the main interact loop.

    Write the test as a generator, yield-ing the input strings, which IPython
    will see as if they were typed in at the prompt.
    """
    def test_method(self):
        testgen = testfunc(self)
        with mock_input_helper(testgen) as mih:
            mih.ip.interact(display_banner=False)

        if mih.exception is not None:
            # Re-raise captured exception
            etype, value, tb = mih.exception
            import traceback
            traceback.print_tb(tb, file=sys.stdout)
            del tb  # Avoid reference loop
            raise value

    return test_method

# Test classes -----------------------------------------------------------------

class InteractiveShellTestCase(unittest.TestCase):
    def rl_hist_entries(self, rl, n):
        """Get last n readline history entries as a list"""
        return [rl.get_history_item(rl.get_current_history_length() - x)
                for x in range(n - 1, -1, -1)]

    def test_runs_without_rl(self):
        """Test that function does not throw without readline"""
        ip = get_ipython()
        ip.has_readline = False
        ip.readline = None
        ip._replace_rlhist_multiline(u'source', 0)

    @skipif(not get_ipython().has_readline, 'no readline')
    def test_runs_without_remove_history_item(self):
        """Test that function does not throw on windows without
           remove_history_item"""
        ip = get_ipython()
        if hasattr(ip.readline, 'remove_history_item'):
            del ip.readline.remove_history_item
        ip._replace_rlhist_multiline(u'source', 0)

    @skipif(not get_ipython().has_readline, 'no readline')
    @skipif(not hasattr(get_ipython().readline, 'remove_history_item'),
            'no remove_history_item')
    def test_replace_multiline_hist_disabled(self):
        """Test that multiline replace does nothing if disabled"""
        ip = get_ipython()
        ip.multiline_history = False

        ghist = [u'line1', u'line2']
        for h in ghist:
           ip.readline.add_history(h)
        hlen_b4_cell = ip.readline.get_current_history_length()
        hlen_b4_cell = ip._replace_rlhist_multiline(u'sourc€\nsource2',
                                                    hlen_b4_cell)

        self.assertEqual(ip.readline.get_current_history_length(),
                          hlen_b4_cell)
        hist = self.rl_hist_entries(ip.readline, 2)
        self.assertEqual(hist, ghist)

    @skipif(not get_ipython().has_readline, 'no readline')
    @skipif(not hasattr(get_ipython().readline, 'remove_history_item'),
            'no remove_history_item')
    def test_replace_multiline_hist_adds(self):
        """Test that multiline replace function adds history"""
        ip = get_ipython()

        hlen_b4_cell = ip.readline.get_current_history_length()
        hlen_b4_cell = ip._replace_rlhist_multiline(u'sourc€', hlen_b4_cell)

        self.assertEqual(hlen_b4_cell,
                          ip.readline.get_current_history_length())

    @skipif(not get_ipython().has_readline, 'no readline')
    @skipif(not hasattr(get_ipython().readline, 'remove_history_item'),
            'no remove_history_item')
    def test_replace_multiline_hist_keeps_history(self):
        """Test that multiline replace does not delete history"""
        ip = get_ipython()
        ip.multiline_history = True

        ghist = [u'line1', u'line2']
        for h in ghist:
           ip.readline.add_history(h)

        #start cell
        hlen_b4_cell = ip.readline.get_current_history_length()
        # nothing added to rl history, should do nothing
        hlen_b4_cell = ip._replace_rlhist_multiline(u'sourc€\nsource2',
                                                    hlen_b4_cell)

        self.assertEqual(ip.readline.get_current_history_length(),
                          hlen_b4_cell)
        hist = self.rl_hist_entries(ip.readline, 2)
        self.assertEqual(hist, ghist)


    @skipif(not get_ipython().has_readline, 'no readline')
    @skipif(not hasattr(get_ipython().readline, 'remove_history_item'),
            'no remove_history_item')
    def test_replace_multiline_hist_replaces_twice(self):
        """Test that multiline entries are replaced twice"""
        ip = get_ipython()
        ip.multiline_history = True

        ip.readline.add_history(u'line0')
        #start cell
        hlen_b4_cell = ip.readline.get_current_history_length()
        ip.readline.add_history('l€ne1')
        ip.readline.add_history('line2')
        #replace cell with single line
        hlen_b4_cell = ip._replace_rlhist_multiline(u'l€ne1\nline2',
                                                    hlen_b4_cell)
        ip.readline.add_history('l€ne3')
        ip.readline.add_history('line4')
        #replace cell with single line
        hlen_b4_cell = ip._replace_rlhist_multiline(u'l€ne3\nline4',
                                                    hlen_b4_cell)

        self.assertEqual(ip.readline.get_current_history_length(),
                          hlen_b4_cell)
        hist = self.rl_hist_entries(ip.readline, 3)
        expected = [u'line0', u'l€ne1\nline2', u'l€ne3\nline4']
        # perform encoding, in case of casting due to ASCII locale
        enc = sys.stdin.encoding or "utf-8"
        expected = [ py3compat.unicode_to_str(e, enc) for e in expected ]
        self.assertEqual(hist, expected)


    @skipif(not get_ipython().has_readline, 'no readline')
    @skipif(not hasattr(get_ipython().readline, 'remove_history_item'),
            'no remove_history_item')
    def test_replace_multiline_hist_replaces_empty_line(self):
        """Test that multiline history skips empty line cells"""
        ip = get_ipython()
        ip.multiline_history = True

        ip.readline.add_history(u'line0')
        #start cell
        hlen_b4_cell = ip.readline.get_current_history_length()
        ip.readline.add_history('l€ne1')
        ip.readline.add_history('line2')
        hlen_b4_cell = ip._replace_rlhist_multiline(u'l€ne1\nline2',
                                                    hlen_b4_cell)
        ip.readline.add_history('')
        hlen_b4_cell = ip._replace_rlhist_multiline(u'', hlen_b4_cell)
        ip.readline.add_history('l€ne3')
        hlen_b4_cell = ip._replace_rlhist_multiline(u'l€ne3', hlen_b4_cell)
        ip.readline.add_history('  ')
        hlen_b4_cell = ip._replace_rlhist_multiline('  ', hlen_b4_cell)
        ip.readline.add_history('\t')
        ip.readline.add_history('\t ')
        hlen_b4_cell = ip._replace_rlhist_multiline('\t', hlen_b4_cell)
        ip.readline.add_history('line4')
        hlen_b4_cell = ip._replace_rlhist_multiline(u'line4', hlen_b4_cell)

        self.assertEqual(ip.readline.get_current_history_length(),
                          hlen_b4_cell)
        hist = self.rl_hist_entries(ip.readline, 4)
        # expect no empty cells in history
        expected = [u'line0', u'l€ne1\nline2', u'l€ne3', u'line4']
        # perform encoding, in case of casting due to ASCII locale
        enc = sys.stdin.encoding or "utf-8"
        expected = [ py3compat.unicode_to_str(e, enc) for e in expected ]
        self.assertEqual(hist, expected)
    
    @mock_input
    def test_inputtransformer_syntaxerror(self):
        ip = get_ipython()
        transformer = SyntaxErrorTransformer()
        ip.input_splitter.python_line_transforms.append(transformer)
        ip.input_transformer_manager.python_line_transforms.append(transformer)

        try:
            #raise Exception
            with tt.AssertPrints('4', suppress=False):
                yield u'print(2*2)'

            with tt.AssertPrints('SyntaxError: input contains', suppress=False):
                yield u'print(2345) # syntaxerror'

            with tt.AssertPrints('16', suppress=False):
                yield u'print(4*4)'

        finally:
            ip.input_splitter.python_line_transforms.remove(transformer)
            ip.input_transformer_manager.python_line_transforms.remove(transformer)


class SyntaxErrorTransformer(InputTransformer):
    def push(self, line):
        pos = line.find('syntaxerror')
        if pos >= 0:
            e = SyntaxError('input contains "syntaxerror"')
            e.text = line
            e.offset = pos + 1
            raise e
        return line

    def reset(self):
        pass

class TerminalMagicsTestCase(unittest.TestCase):
    def test_paste_magics_message(self):
        """Test that an IndentationError while using paste magics doesn't
        trigger a message about paste magics and also the opposite."""

        ip = get_ipython()
        s = ('for a in range(5):\n'
             'print(a)')

        tm = ip.magics_manager.registry['TerminalMagics']
        with tt.AssertPrints("If you want to paste code into IPython, try the "
                "%paste and %cpaste magic functions."):
            ip.run_cell(s)

        with tt.AssertNotPrints("If you want to paste code into IPython, try the "
                "%paste and %cpaste magic functions."):
            tm.store_or_execute(s, name=None)

    def test_paste_magics_blankline(self):
        """Test that code with a blank line doesn't get split (gh-3246)."""
        ip = get_ipython()
        s = ('def pasted_func(a):\n'
             '    b = a+1\n'
             '\n'
             '    return b')
        
        tm = ip.magics_manager.registry['TerminalMagics']
        tm.store_or_execute(s, name=None)
        
        self.assertEqual(ip.user_ns['pasted_func'](54), 55)
