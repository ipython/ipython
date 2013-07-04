"""Tests for two-process terminal frontend

Currenlty only has the most simple test possible, starting a console and running
a single command.

Authors:

* Min RK
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time

import nose.tools as nt
from nose import SkipTest

from IPython.testing import decorators as dec
from IPython.utils import py3compat
from IPython.utils.process import find_cmd

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

@dec.skip_win32
def test_console_starts():
    """test that `ipython console` starts a terminal"""
    from IPython.external import pexpect
    
    # weird IOErrors prevent this from firing sometimes:
    ipython_cmd = None
    for i in range(5):
        try:
            ipython_cmd = find_cmd('ipython3' if py3compat.PY3 else 'ipython')
        except IOError:
            time.sleep(0.1)
        else:
            break
    if ipython_cmd is None:
        raise SkipTest("Could not determine ipython command")
    
    p = pexpect.spawn(ipython_cmd, args=['console', '--colors=NoColor'])
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=15)
    nt.assert_equal(idx, 0, "expected in prompt")
    p.sendline('5')
    idx = p.expect([r'Out\[\d+\]: 5', pexpect.EOF], timeout=5)
    nt.assert_equal(idx, 0, "expected out prompt")
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=5)
    nt.assert_equal(idx, 0, "expected second in prompt")
    # send ctrl-D;ctrl-D to exit
    p.sendeof()
    p.sendeof()
    p.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=5)
    if p.isalive():
        p.terminate()
