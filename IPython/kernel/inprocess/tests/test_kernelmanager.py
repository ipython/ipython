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
from IPython.kernel.inprocess.blocking import BlockingInProcessKernelClient
from IPython.kernel.inprocess.manager import InProcessKernelManager

#-----------------------------------------------------------------------------
# Test case
#-----------------------------------------------------------------------------

class InProcessKernelManagerTestCase(unittest.TestCase):

    def test_interface(self):
        """ Does the in-process kernel manager implement the basic KM interface?
        """
        km = InProcessKernelManager()
        self.assert_(not km.has_kernel)

        km.start_kernel()
        self.assert_(km.has_kernel)
        self.assert_(km.kernel is not None)

        kc = BlockingInProcessKernelClient(kernel=km.kernel)
        self.assert_(not kc.channels_running)

        kc.start_channels()
        self.assert_(kc.channels_running)

        old_kernel = km.kernel
        km.restart_kernel()
        self.assertIsNotNone(km.kernel)
        self.assertNotEquals(km.kernel, old_kernel)

        km.shutdown_kernel()
        self.assert_(not km.has_kernel)

        self.assertRaises(NotImplementedError, km.interrupt_kernel)
        self.assertRaises(NotImplementedError, km.signal_kernel, 9)

        kc.stop_channels()
        self.assert_(not kc.channels_running)

    def test_execute(self):
        """ Does executing code in an in-process kernel work?
        """
        km = InProcessKernelManager()
        km.start_kernel()
        kc = BlockingInProcessKernelClient(kernel=km.kernel)
        kc.start_channels()
        kc.execute('foo = 1')
        self.assertEquals(km.kernel.shell.user_ns['foo'], 1)

    def test_complete(self):
        """ Does requesting completion from an in-process kernel work?
        """
        km = InProcessKernelManager()
        km.start_kernel()
        kc = BlockingInProcessKernelClient(kernel=km.kernel)
        kc.start_channels()
        km.kernel.shell.push({'my_bar': 0, 'my_baz': 1})
        kc.complete('my_ba', 'my_ba', 5)
        msg = kc.get_shell_msg()
        self.assertEqual(msg['header']['msg_type'], 'complete_reply')
        self.assertEqual(sorted(msg['content']['matches']),
                          ['my_bar', 'my_baz'])

    def test_object_info(self):
        """ Does requesting object information from an in-process kernel work?
        """
        km = InProcessKernelManager()
        km.start_kernel()
        kc = BlockingInProcessKernelClient(kernel=km.kernel)
        kc.start_channels()
        km.kernel.shell.user_ns['foo'] = 1
        kc.object_info('foo')
        msg = kc.get_shell_msg()
        self.assertEquals(msg['header']['msg_type'], 'object_info_reply')
        self.assertEquals(msg['content']['name'], 'foo')
        self.assertEquals(msg['content']['type_name'], 'int')

    def test_history(self):
        """ Does requesting history from an in-process kernel work?
        """
        km = InProcessKernelManager()
        km.start_kernel()
        kc = BlockingInProcessKernelClient(kernel=km.kernel)
        kc.start_channels()
        kc.execute('%who')
        kc.history(hist_access_type='tail', n=1)
        msg = kc.shell_channel.get_msgs()[-1]
        self.assertEquals(msg['header']['msg_type'], 'history_reply')
        history = msg['content']['history']
        self.assertEquals(len(history), 1)
        self.assertEquals(history[0][2], '%who')


if __name__ == '__main__':
    unittest.main()
