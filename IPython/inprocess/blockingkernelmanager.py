""" Implements a fully blocking kernel manager.

Useful for test suites and blocking terminal interfaces.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Local imports.
from IPython.utils.io import raw_print
from IPython.utils.traitlets import Type
from kernelmanager import InProcessKernelManager, InProcessShellChannel, \
    InProcessIOPubChannel, InProcessStdInChannel
from IPython.zmq.blockingkernelmanager import BlockingChannelMixin


#-----------------------------------------------------------------------------
# Blocking kernel manager
#-----------------------------------------------------------------------------

class BlockingInProcessShellChannel(BlockingChannelMixin, InProcessShellChannel):
    pass

class BlockingInProcessIOPubChannel(BlockingChannelMixin, InProcessIOPubChannel):
    pass

class BlockingInProcessStdInChannel(BlockingChannelMixin, InProcessStdInChannel):
    
    def call_handlers(self, msg):
        """ Overridden for the in-process channel.

        This methods simply calls raw_input directly.
        """
        msg_type = msg['header']['msg_type']
        if msg_type == 'input_request':
            _raw_input = self.manager.kernel._sys_raw_input
            prompt = msg['content']['prompt']
            raw_print(prompt, end='')
            self.input(_raw_input())

class BlockingInProcessKernelManager(InProcessKernelManager):

    # The classes to use for the various channels.
    shell_channel_class = Type(BlockingInProcessShellChannel)
    iopub_channel_class = Type(BlockingInProcessIOPubChannel)
    stdin_channel_class = Type(BlockingInProcessStdInChannel)
