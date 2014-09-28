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

from nose import SkipTest

import IPython.testing.tools as tt
from IPython.testing import decorators as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

@dec.skip_win32
def test_console_starts():
    """test that `ipython console` starts a terminal"""
    p, pexpect, t = start_console()
    p.sendline('5')
    idx = p.expect([r'Out\[\d+\]: 5', pexpect.EOF], timeout=t)
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=t)
    stop_console(p, pexpect, t)

def test_help_output():
    """ipython console --help-all works"""
    tt.help_all_output_test('console')


def test_display_text():
    "Ensure display protocol plain/text key is supported"
    # equivalent of:
    #
    #   x = %lsmagic
    #   from IPython.display import display; display(x);
    p, pexpect, t = start_console()
    p.sendline('x = %lsmagic')
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=t)
    p.sendline('from IPython.display import display; display(x);')
    p.expect([r'Available line magics:', pexpect.EOF], timeout=t)
    stop_console(p, pexpect, t)

def stop_console(p, pexpect, t):
    "Stop a running `ipython console` running via pexpect"
    # send ctrl-D;ctrl-D to exit
    p.sendeof()
    p.sendeof()
    p.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=t)
    if p.isalive():
        p.terminate()


def start_console():
    "Start `ipython console` using pexpect"
    from IPython.external import pexpect
    
    args = ['-m', 'IPython', 'console', '--colors=NoColor']
    cmd = sys.executable
    
    try:
        p = pexpect.spawn(cmd, args=args)
    except IOError:
        raise SkipTest("Couldn't find command %s" % cmd)
    
    # timeout after one minute
    t = 60
    idx = p.expect([r'In \[\d+\]', pexpect.EOF], timeout=t)
    return p, pexpect, t
