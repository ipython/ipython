# -*- coding: utf-8 -*-
"""Tests for the TerminalInteractiveShell and related pieces."""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import unittest

from IPython.core.inputtransformer import InputTransformer
from IPython.testing import tools as tt
from IPython.utils import tokenize2

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
        self.orig_prompt_for_code = self.ip.prompt_for_code
        self.ip.prompt_for_code = self.fake_input
        return self

    def __exit__(self, etype, value, tb):
        self.ip.prompt_for_code = self.orig_prompt_for_code

    def fake_input(self):
        try:
            return next(self.testgen)
        except StopIteration:
            self.ip.keep_running = False
            return u''
        except:
            self.exception = sys.exc_info()
            self.ip.keep_running = False
            return u''

def mock_input(testfunc):
    """Decorator for tests of the main interact loop.

    Write the test as a generator, yield-ing the input strings, which IPython
    will see as if they were typed in at the prompt.
    """
    def test_method(self):
        testgen = testfunc(self)
        with mock_input_helper(testgen) as mih:
            mih.ip.interact()

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

    def test_plain_text_only(self):
        ip = get_ipython()
        formatter = ip.display_formatter
        assert formatter.active_types == ['text/plain']

    def test_triple_quited_strings_with_backslash_issue9841(self):
        def get_line(data=['"""\nabc\ndef\\\n"""\n']):
            if not data:
                raise tokenize2.TokenError
            return data.pop()

        tokens = []
        try:
            for intok in tokenize2.generate_tokens(get_line):
                tokens.append(intok)
            else:
                assert False

        except tokenize2.TokenError:
            assert len(tokens) == 2
            assert tokens[0][0] == tokenize2.STRING
            assert tokens[0][1] == '"""\nabc\ndef\\\n"""'
            assert tokens[1][0] == tokenize2.NEWLINE


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
