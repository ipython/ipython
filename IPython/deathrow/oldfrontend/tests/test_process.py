# encoding: utf-8
"""
Test process execution and IO redirection.
"""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from cStringIO import StringIO
from time import sleep
import sys

from IPython.frontend.process import PipedProcess
from IPython.testing import decorators as dec


def test_capture_out():
    """ A simple test to see if we can execute a process and get the output.
    """
    s = StringIO()
    p = PipedProcess('echo 1', out_callback=s.write, )
    p.start()
    p.join()
    result = s.getvalue().rstrip()
    assert result == '1'


def test_io():
    """ Checks that we can send characters on stdin to the process.
    """
    s = StringIO()
    p = PipedProcess(sys.executable + ' -c "a = raw_input(); print a"',
                            out_callback=s.write, )
    p.start()
    test_string = '12345\n'
    while not hasattr(p, 'process'):
        sleep(0.1)
    p.process.stdin.write(test_string)
    p.join()
    result = s.getvalue()
    assert result == test_string


@dec.skip_win32
def test_kill():
    """ Check that we can kill a process, and its subprocess.
    """
    s = StringIO()
    p = PipedProcess(sys.executable + ' -c "a = raw_input();"',
                            out_callback=s.write, )
    p.start()
    while not hasattr(p, 'process'):
        sleep(0.1)
    p.process.kill()
    assert p.process.poll() is not None


if __name__ == '__main__':
    test_capture_out()
    test_io()
    test_kill()

