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

    edit_buffer = ''


    def __init__(self):
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

    def new_prompt(self, prompt):
        self.edit_buffer = ''
        PrefilterFrontEnd.new_prompt(self, prompt)


def test_execution():
    """ Test execution of a command.
    """
    f = TestPrefilterFrontEnd()
    f.edit_buffer='print 1\n'
    f._on_enter()
    assert f.out.getvalue() == '1\n'


def test_multiline():
    """ Test execution of a multiline command.
    """
    f = TestPrefilterFrontEnd()
    f.edit_buffer='if True:'
    f._on_enter()
    f.add_to_edit_buffer('print 1')
    f._on_enter()
    assert f.out.getvalue() == ''
    f._on_enter()
    assert f.out.getvalue() == '1\n'
    f = TestPrefilterFrontEnd()
    f.edit_buffer='(1 +'
    f._on_enter()
    f.add_to_edit_buffer('0)')
    f._on_enter()
    assert f.out.getvalue() == ''
    f._on_enter()
    assert f.out.getvalue() == '1\n'


def test_capture():
    """ Test the capture of output in different channels.
    """
    # Test on the OS-level stdout, stderr.
    f = TestPrefilterFrontEnd()
    f.edit_buffer='import os; out=os.fdopen(1, "w"); out.write("1") ; out.flush()'
    f._on_enter()
    assert f.out.getvalue() == '1'
    f = TestPrefilterFrontEnd()
    f.edit_buffer='import os; out=os.fdopen(2, "w"); out.write("1") ; out.flush()'
    f._on_enter()
    assert f.out.getvalue() == '1'

     
def test_magic():
    """ Test the magic expansion and history.
    
        This test is fairly fragile and will break when magics change.
    """
    f = TestPrefilterFrontEnd()
    f.add_to_edit_buffer('%who\n')
    f._on_enter()
    assert f.out.getvalue() == 'Interactive namespace is empty.\n'


def test_help():
    """ Test object inspection.
    """
    f = TestPrefilterFrontEnd()
    f.add_to_edit_buffer("def f():")
    f._on_enter()
    f.add_to_edit_buffer("'foobar'")
    f._on_enter()
    f.add_to_edit_buffer("pass")
    f._on_enter()
    f._on_enter()
    f.add_to_edit_buffer("f?")
    f._on_enter()
    assert f.out.getvalue().split()[-1] == 'foobar' 

def test_completion():
    """ Test command-line completion.
    """
    f = TestPrefilterFrontEnd()
    f.edit_buffer = 'zzza = 1'
    f._on_enter()
    f.edit_buffer = 'zzzb = 2'
    f._on_enter()
    f.edit_buffer = 'zz'


if __name__ == '__main__':
    test_magic()
    test_help()
    test_execution()
    test_multiline()
    test_capture()
