# encoding: utf-8
"""
Test process execution and IO redirection.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

from IPython.frontend.prefilterfrontend import PrefilterFrontEnd
from cStringIO import StringIO
import string
import sys

class TestPrefilterFrontEnd(PrefilterFrontEnd):
    
    input_prompt_template = string.Template('')
    output_prompt_template = string.Template('')

    def __init__(self):
        self.out = StringIO()
        PrefilterFrontEnd.__init__(self)

    def write(self, string):
       self.out.write(string) 

    def _on_enter(self):
        self.input_buffer += '\n'
        PrefilterFrontEnd._on_enter(self)


def test_execution():
    """ Test execution of a command.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer = 'print 1\n'
    f._on_enter()
    assert f.out.getvalue() == '1\n'


def test_multiline():
    """ Test execution of a multiline command.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer = 'if True:'
    f._on_enter()
    f.input_buffer += 'print 1'
    f._on_enter()
    assert f.out.getvalue() == ''
    f._on_enter()
    assert f.out.getvalue() == '1\n'
    f = TestPrefilterFrontEnd()
    f.input_buffer='(1 +'
    f._on_enter()
    f.input_buffer += '0)'
    f._on_enter()
    assert f.out.getvalue() == ''
    f._on_enter()
    assert f.out.getvalue() == '1\n'


def test_capture():
    """ Test the capture of output in different channels.
    """
    # Test on the OS-level stdout, stderr.
    f = TestPrefilterFrontEnd()
    f.input_buffer = \
            'import os; out=os.fdopen(1, "w"); out.write("1") ; out.flush()'
    f._on_enter()
    assert f.out.getvalue() == '1'
    f = TestPrefilterFrontEnd()
    f.input_buffer = \
            'import os; out=os.fdopen(2, "w"); out.write("1") ; out.flush()'
    f._on_enter()
    assert f.out.getvalue() == '1'

     
def test_magic():
    """ Test the magic expansion and history.
    
        This test is fairly fragile and will break when magics change.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer += '%who\n'
    f._on_enter()
    assert f.out.getvalue() == 'Interactive namespace is empty.\n'


def test_help():
    """ Test object inspection.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer += "def f():"
    f._on_enter()
    f.input_buffer += "'foobar'"
    f._on_enter()
    f.input_buffer += "pass"
    f._on_enter()
    f._on_enter()
    f.input_buffer += "f?"
    f._on_enter()
    assert f.out.getvalue().split()[-1] == 'foobar' 


def test_completion():
    """ Test command-line completion.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer = 'zzza = 1'
    f._on_enter()
    f.input_buffer = 'zzzb = 2'
    f._on_enter()
    f.input_buffer = 'zz'
    f.complete_current_input()
    assert f.out.getvalue() == '\nzzza zzzb '
    assert f.input_buffer == 'zzz'


if __name__ == '__main__':
    test_magic()
    test_help()
    test_execution()
    test_multiline()
    test_capture()
    test_completion()
