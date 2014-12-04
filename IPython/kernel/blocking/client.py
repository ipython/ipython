"""Implements a fully blocking kernel client.

Useful for test suites and blocking terminal interfaces.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

try:
    from queue import Empty  # Python 3
except ImportError:
    from Queue import Empty  # Python 2

from IPython.utils.traitlets import Type
from IPython.kernel.client import KernelClient
from .channels import (
    BlockingIOPubChannel, BlockingHBChannel,
    BlockingShellChannel, BlockingStdInChannel
)

class BlockingKernelClient(KernelClient):
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

    # The classes to use for the various channels
    shell_channel_class = Type(BlockingShellChannel)
    iopub_channel_class = Type(BlockingIOPubChannel)
    stdin_channel_class = Type(BlockingStdInChannel)
    hb_channel_class = Type(BlockingHBChannel)
