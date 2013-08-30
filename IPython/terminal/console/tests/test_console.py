"""Tests for two-process terminal frontend

Currently only has the most simple test possible, starting a console and running
a single command.

Authors:

* Min RK
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import time

import nose.tools as nt
from nose import SkipTest

import IPython.testing.tools as tt
from IPython.testing import decorators as dec
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

@dec.skip_win32
def test_console_starts():
    """test that `ipython console` starts a terminal"""
    from IPython.external import pexpect
    
    args = ['console', '--colors=NoColor']
    # FIXME: remove workaround for 2.6 support
    if sys.version_info[:2] > (2,6):
        args = ['-m', 'IPython'] + args
        cmd = sys.executable
    else:
        cmd = 'ipython'
    
    try:
        p = pexpect.spawn(cmd, args=args)
    except IOError:
        raise SkipTest("Couldn't find command %s" % cmd)
    
    # timeout after one minute
    t = 60
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=t)
    p.sendline('5')
    idx = p.expect([r'Out\[\d+\]: 5', pexpect.EOF], timeout=t)
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=t)
    # send ctrl-D;ctrl-D to exit
    p.sendeof()
    p.sendeof()
    p.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=t)
    if p.isalive():
        p.terminate()

def test_help_output():
    """ipython console --help-all works"""
    tt.help_all_output_test('console')

