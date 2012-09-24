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
import unittest

# Local imports
from IPython.inprocess.blockingkernelmanager import \
    BlockingInProcessKernelManager
from IPython.inprocess.ipkernel import InProcessKernel
from IPython.utils.io import capture_output

#-----------------------------------------------------------------------------
# Test case
#-----------------------------------------------------------------------------

class InProcessKernelTestCase(unittest.TestCase):

    def test_pylab(self):
        """ Does pylab work in the in-process kernel?
        """
        km = BlockingInProcessKernelManager()
        km.start_kernel()
        km.shell_channel.execute('%pylab')
        msg = get_stream_message(km)
        self.assert_('Welcome to pylab' in msg['content']['data'])

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
