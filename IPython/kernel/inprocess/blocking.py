""" Implements a fully blocking kernel client.

Useful for test suites and blocking terminal interfaces.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

try:
    from queue import Queue, Empty  # Py 3
except ImportError:
    from Queue import Queue, Empty  # Py 2

# IPython imports
from IPython.utils.io import raw_print
from IPython.utils.traitlets import Type
#from IPython.kernel.blocking.channels import BlockingChannelMixin

# Local imports
from .channels import (
    InProcessChannel,
)
from .client import InProcessKernelClient

class BlockingInProcessChannel(InProcessChannel):

    def __init__(self, *args, **kwds):
        super(BlockingInProcessChannel, self).__init__(*args, **kwds)
        self._in_queue = Queue()

    def call_handlers(self, msg):
        self._in_queue.put(msg)

    def get_msg(self, block=True, timeout=None):
        """ Gets a message if there is one that is ready. """
        if timeout is None:
            # Queue.get(timeout=None) has stupid uninteruptible
            # behavior, so wait for a week instead
            timeout = 604800
        return self._in_queue.get(block, timeout)

    def get_msgs(self):
        """ Get all messages that are currently ready. """
        msgs = []
        while True:
            try:
                msgs.append(self.get_msg(block=False))
            except Empty:
                break
        return msgs

    def msg_ready(self):
        """ Is there a message that has been received? """
        return not self._in_queue.empty()


class BlockingInProcessStdInChannel(BlockingInProcessChannel):
    def call_handlers(self, msg):
        """ Overridden for the in-process channel.

        This methods simply calls raw_input directly.
        """
        msg_type = msg['header']['msg_type']
        if msg_type == 'input_request':
            _raw_input = self.client.kernel._sys_raw_input
            prompt = msg['content']['prompt']
            raw_print(prompt, end='')
            self.client.input(_raw_input())

class BlockingInProcessKernelClient(InProcessKernelClient):

    # The classes to use for the various channels.
    shell_channel_class = Type(BlockingInProcessChannel)
    iopub_channel_class = Type(BlockingInProcessChannel)
    stdin_channel_class = Type(BlockingInProcessStdInChannel)

    def wait_for_ready(self):
        # Wait for kernel info reply on shell channel
        while True:
            msg = self.shell_channel.get_msg(block=True)
            if msg['msg_type'] == 'kernel_info_reply':
                self._handle_kernel_info_reply(msg)
                break

        # Flush IOPub channel
        while True:
            try:
                msg = self.iopub_channel.get_msg(block=True, timeout=0.2)
                print(msg['msg_type'])
            except Empty:
                break
