#-------------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports
from StringIO import StringIO
import sys
import unittest

# Local imports
from IPython.inprocess.blockingkernelmanager import \
    BlockingInProcessKernelManager
from IPython.inprocess.ipkernel import InProcessKernel
from IPython.testing.decorators import skipif_not_matplotlib
from IPython.utils.io import capture_output
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Test case
#-----------------------------------------------------------------------------

class InProcessKernelTestCase(unittest.TestCase):

    @skipif_not_matplotlib
    def test_pylab(self):
        """ Does pylab work in the in-process kernel?
        """
        km = BlockingInProcessKernelManager()
        km.start_kernel()
        km.shell_channel.execute('%pylab')
        msg = get_stream_message(km)
        self.assert_('Welcome to pylab' in msg['content']['data'])

    def test_raw_input(self):
        """ Does the in-process kernel handle raw_input correctly?
        """
        km = BlockingInProcessKernelManager()
        km.start_kernel()

        io = StringIO('foobar\n')
        sys_stdin = sys.stdin
        sys.stdin = io
        try:
            if py3compat.PY3:
                km.shell_channel.execute('x = input()')
            else:
                km.shell_channel.execute('x = raw_input()')
        finally:
            sys.stdin = sys_stdin
        self.assertEqual(km.kernel.shell.user_ns.get('x'), 'foobar')

    def test_stdout(self):
        """ Does the in-process kernel correctly capture IO?
        """
        kernel = InProcessKernel()

        with capture_output() as io:
            kernel.shell.run_cell('print("foo")')
        self.assertEqual(io.stdout, 'foo\n')

        km = BlockingInProcessKernelManager(kernel=kernel)
        kernel.frontends.append(km)
        km.shell_channel.execute('print("bar")')
        msg = get_stream_message(km)
        self.assertEqual(msg['content']['data'], 'bar\n')

#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

def get_stream_message(kernel_manager, timeout=5):
    """ Gets a single stream message synchronously from the sub channel.
    """
    while True:
        msg = kernel_manager.sub_channel.get_msg(timeout=timeout)
        if msg['header']['msg_type'] == 'stream':
            return msg


if __name__ == '__main__':
    unittest.main()
