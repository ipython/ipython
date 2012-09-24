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

#-----------------------------------------------------------------------------
# Test case
#-----------------------------------------------------------------------------

class InProcessKernelManagerTestCase(unittest.TestCase):

    def test_inteface(self):
        """ Does the in-process kernel manager implement the basic KM interface?
        """
        km = BlockingInProcessKernelManager()
        self.assert_(not km.channels_running)
        self.assert_(not km.has_kernel)

        km.start_channels()
        self.assert_(km.channels_running)

        km.start_kernel()
        self.assert_(km.has_kernel)
        self.assert_(km.kernel is not None)

        old_kernel = km.kernel
        km.restart_kernel()
        self.assert_(km.kernel is not None)
        self.assertNotEquals(km.kernel, old_kernel)

        km.shutdown_kernel()
        self.assert_(not km.has_kernel)

        self.assertRaises(NotImplementedError, km.interrupt_kernel)
        self.assertRaises(NotImplementedError, km.signal_kernel, 9)

        km.stop_channels()
        self.assert_(not km.channels_running)

    def test_execute(self):
        """ Does executing code in an in-process kernel work?
        """
        km = BlockingInProcessKernelManager()
        km.start_kernel()
        km.shell_channel.execute('foo = 1')
        self.assertEquals(km.kernel.shell.user_ns['foo'], 1)

    def test_object_info(self):
        """ Does requesting object information from an in-process kernel work?
        """
        km = BlockingInProcessKernelManager()
        km.start_kernel()
        km.kernel.shell.user_ns['foo'] = 1
        km.shell_channel.object_info('foo')
        msg = km.shell_channel.get_msg()
        self.assertEquals(msg['header']['msg_type'], 'object_info_reply')
        self.assertEquals(msg['content']['name'], 'foo')
        self.assertEquals(msg['content']['type_name'], 'int')


if __name__ == '__main__':
    unittest.main()
