"""Test embedding of IPython"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
import nose.tools as nt
from IPython.utils.process import process_handler
from IPython.utils.tempdir import NamedFileInTemporaryDirectory
from IPython.testing.decorators import skip_win32

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


_sample_embed = b"""
from __future__ import print_function
import IPython

a = 3
b = 14
print(a, '.', b)

IPython.embed()

print('bye!')
"""

_exit = b"exit\r"

def test_ipython_embed():
    """test that `IPython.embed()` works"""
    with NamedFileInTemporaryDirectory('file_with_embed.py') as f:
        f.write(_sample_embed)
        f.flush()
        f.close() # otherwise msft won't be able to read the file

        # run `python file_with_embed.py`
        cmd = [sys.executable, f.name]

        out, p = process_handler(cmd, lambda p: (p.communicate(_exit), p))
        std = out[0].decode('UTF-8')
        nt.assert_equal(p.returncode, 0)
        nt.assert_in('3 . 14', std)
        if os.name != 'nt':
            # TODO: Fix up our different stdout references, see issue gh-14
            nt.assert_in('IPython', std)
        nt.assert_in('bye!', std)

@skip_win32
def test_nest_embed():
    """test that `IPython.embed()` is nestable"""
    import pexpect
    ipy_prompt = r']:' #ansi color codes give problems matching beyond this


    child = pexpect.spawn('%s -m IPython --colors=nocolor'%(sys.executable, ))
    child.expect(ipy_prompt)
    child.sendline("from __future__ import print_function")
    child.expect(ipy_prompt)
    child.sendline("import IPython")
    child.expect(ipy_prompt)
    child.sendline("ip0 = get_ipython()")
    #enter first nested embed
    child.sendline("IPython.embed()")
    #skip the banner until we get to a prompt
    try:
        prompted = -1
        while prompted != 0:
            prompted = child.expect([ipy_prompt, '\r\n'])
    except pexpect.TIMEOUT as e:
        print(e)
        #child.interact()
    child.sendline("embed1 = get_ipython()"); child.expect(ipy_prompt)
    child.sendline("print('true' if embed1 is not ip0 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline("print('true' if IPython.get_ipython() is embed1 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    #enter second nested embed
    child.sendline("IPython.embed()")
    #skip the banner until we get to a prompt
    try:
        prompted = -1
        while prompted != 0:
            prompted = child.expect([ipy_prompt, '\r\n'])
    except pexpect.TIMEOUT as e:
        print(e)
        #child.interact()
    child.sendline("embed2 = get_ipython()"); child.expect(ipy_prompt)
    child.sendline("print('true' if embed2 is not embed1 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline("print('true' if embed2 is IPython.get_ipython() else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline('exit')
    #back at first embed
    child.expect(ipy_prompt)
    child.sendline("print('true' if get_ipython() is embed1 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline("print('true' if IPython.get_ipython() is embed1 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline('exit')
    #back at launching scope
    child.expect(ipy_prompt)
    child.sendline("print('true' if get_ipython() is ip0 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline("print('true' if IPython.get_ipython() is ip0 else 'false')")
    assert(child.expect(['true\r\n', 'false\r\n']) == 0)
    child.expect(ipy_prompt)
    child.sendline('exit')
    child.close()
