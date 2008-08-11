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

class TestPrefilterFrontEnd(PrefilterFrontEnd):
    
    input_prompt_template = string.Template('')
    output_prompt_template = string.Template('')


    def __init__(self, edit_buffer=''):
        self.edit_buffer = edit_buffer
        self.out = StringIO()
        PrefilterFrontEnd.__init__(self)

    def get_current_edit_buffer(self):
        return self.edit_buffer

    def add_to_edit_buffer(self, string):
        self.edit_buffer += string

    def write(self, string):
       self.out.write(string) 

    def _on_enter(self):
        self.add_to_edit_buffer('\n')
        PrefilterFrontEnd._on_enter(self)


def test_execution():
    """ Test execution of a command.
    """
    f = TestPrefilterFrontEnd(edit_buffer='print 1\n')
    f._on_enter()
    assert f.out.getvalue() == '1\n'


def test_multiline():
    """ Test execution of a multiline command.
    """
    f = TestPrefilterFrontEnd(edit_buffer='if True:')
    f._on_enter()
    f.add_to_edit_buffer('print 1')
    f._on_enter()
    assert f.out.getvalue() == ''
    f._on_enter()
    assert f.out.getvalue() == '1\n'
    f = TestPrefilterFrontEnd(edit_buffer='(1 +')
    f._on_enter()
    f.add_to_edit_buffer('0)')
    f._on_enter()
    assert f.out.getvalue() == ''
    f._on_enter()
    assert f.out.getvalue() == '1\n'


def test_capture():
    """ Test the capture of output in different channels.
    """
    f = TestPrefilterFrontEnd(
            edit_buffer='import os; out=os.fdopen(1, "w"); out.write("1")')
    f._on_enter()
    f._on_enter()
    assert f.out.getvalue() == '1'
    f = TestPrefilterFrontEnd(
            edit_buffer='import os; out=os.fdopen(2, "w"); out.write("1")')
    f._on_enter()
    f._on_enter()
    assert f.out.getvalue() == '1'
     


if __name__ == '__main__':
    test_execution()
    test_multiline()
    test_capture()
