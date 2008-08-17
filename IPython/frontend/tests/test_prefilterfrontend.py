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

from cStringIO import StringIO
import string

from IPython.ipapi import get as get_ipython0
from IPython.frontend.prefilterfrontend import PrefilterFrontEnd
from copy import deepcopy

class TestPrefilterFrontEnd(PrefilterFrontEnd):
    
    input_prompt_template = string.Template('')
    output_prompt_template = string.Template('')
    banner = ''

    def __init__(self):
        ipython0 = get_ipython0().IP
        self.out = StringIO()
        PrefilterFrontEnd.__init__(self, ipython0=ipython0)
        # Clean up the namespace for isolation between tests
        user_ns = self.ipython0.user_ns
        # We need to keep references to things so that they don't
        # get garbage collected (this stinks).
        self.shadow_ns = dict()
        for i in self.ipython0.magic_who_ls():
            self.shadow_ns[i] = user_ns.pop(i)
        # Some more code for isolation (yeah, crazy)
        self._on_enter()
        self.out.flush()
        self.out.reset()
        self.out.truncate()

    def write(self, string, *args, **kwargs):
       self.out.write(string) 

    def _on_enter(self):
        self.input_buffer += '\n'
        PrefilterFrontEnd._on_enter(self)


def isolate_ipython0(func):
    """ Decorator to isolate execution that involves an iptyhon0.
    """
    def my_func(*args, **kwargs):
        ipython0 = get_ipython0().IP
        user_ns = deepcopy(ipython0.user_ns)
        global_ns = deepcopy(ipython0.global_ns)
        try:
            func(*args, **kwargs)
        finally:
            ipython0.user_ns = user_ns
            ipython0.global_ns = global_ns

    return my_func


@isolate_ipython0
def test_execution():
    """ Test execution of a command.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer = 'print 1'
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value  == '1\n'


@isolate_ipython0
def test_multiline():
    """ Test execution of a multiline command.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer = 'if True:'
    f._on_enter()
    f.input_buffer += 'print 1'
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == ''
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == '1\n'
    f = TestPrefilterFrontEnd()
    f.input_buffer='(1 +'
    f._on_enter()
    f.input_buffer += '0)'
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == ''
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == '1\n'


@isolate_ipython0
def test_capture():
    """ Test the capture of output in different channels.
    """
    # Test on the OS-level stdout, stderr.
    f = TestPrefilterFrontEnd()
    f.input_buffer = \
            'import os; out=os.fdopen(1, "w"); out.write("1") ; out.flush()'
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == '1'
    f = TestPrefilterFrontEnd()
    f.input_buffer = \
            'import os; out=os.fdopen(2, "w"); out.write("1") ; out.flush()'
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == '1'

     
@isolate_ipython0
def test_magic():
    """ Test the magic expansion and history.
    
        This test is fairly fragile and will break when magics change.
    """
    f = TestPrefilterFrontEnd()
    f.input_buffer += '%who'
    f._on_enter()
    out_value = f.out.getvalue()
    assert out_value == 'Interactive namespace is empty.\n'


@isolate_ipython0
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
    assert 'traceback' not in f.last_result
    ## XXX: ipython doctest magic breaks this. I have no clue why
    #out_value = f.out.getvalue()
    #assert out_value.split()[-1] == 'foobar' 


@isolate_ipython0
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
    out_value = f.out.getvalue()
    assert out_value == '\nzzza zzzb '
    assert f.input_buffer == 'zzz'


if __name__ == '__main__':
    test_magic()
    test_help()
    test_execution()
    test_multiline()
    test_capture()
    test_completion()
