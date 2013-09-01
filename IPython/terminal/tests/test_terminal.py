# coding: utf-8
"""Tests for the IPython terminal"""

import os
import tempfile
import shutil

import nose.tools as nt

from IPython.testing.tools import make_tempfile, ipexec


TEST_SYNTAX_ERROR_CMDS = """
from IPython.core.inputtransformer import InputTransformer

%cpaste
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
--

ip = get_ipython()
transformer = SyntaxErrorTransformer()
ip.input_splitter.python_line_transforms.append(transformer)
ip.input_transformer_manager.python_line_transforms.append(transformer)

# now the actual commands
1234
2345  # syntaxerror <- triggered here
3456
"""

def test_syntax_error():
    """Check that the IPython terminal does not abort if a SyntaxError is raised in an InputTransformer"""
    try:
        tmp = tempfile.mkdtemp()
        filename = os.path.join(tmp, 'test_syntax_error.py')
        with open(filename, 'w') as f:
            f.write(TEST_SYNTAX_ERROR_CMDS)
        out, err = ipexec(filename, pipe=True)
        nt.assert_equal(err, '')
        nt.assert_in('1234', out)
        nt.assert_in('    2345  # syntaxerror <- triggered here', out)
        nt.assert_in('            ^', out)
        nt.assert_in('SyntaxError: input contains "syntaxerror"', out)
        nt.assert_in('3456', out)
    finally:
        shutil.rmtree(tmp)
