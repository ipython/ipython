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

# Standard library imports.
import Queue
from threading import Event

# Local imports.
from IPython.utils.traitlets import Type
from kernelmanager import EmbeddedKernelManager, ShellEmbeddedChannel, \
    SubEmbeddedChannel, StdInEmbeddedChannel

#-----------------------------------------------------------------------------
# Utility classes
#-----------------------------------------------------------------------------

class BlockingChannelMixin(object):
    
    def __init__(self, *args, **kwds):
        super(BlockingChannelMixin, self).__init__(*args, **kwds)
        self._in_queue = Queue.Queue()
        
    def call_handlers(self, msg):
        self._in_queue.put(msg)
        
    def get_msg(self, block=True, timeout=None):
        """ Gets a message if there is one that is ready. """
        return self._in_queue.get(block, timeout)
        
    def get_msgs(self):
        """ Get all messages that are currently ready. """
        msgs = []
        while True:
            try:
                msgs.append(self.get_msg(block=False))
            except Queue.Empty:
                break
        return msgs
    
    def msg_ready(self):
        """ Is there a message that has been received? """
        return not self._in_queue.empty()

#-----------------------------------------------------------------------------
# Blocking kernel manager
#-----------------------------------------------------------------------------

class BlockingShellEmbeddedChannel(BlockingChannelMixin, ShellEmbeddedChannel):
    pass

class BlockingSubEmbeddedChannel(BlockingChannelMixin, SubEmbeddedChannel):
    pass

class BlockingStdInEmbeddedChannel(BlockingChannelMixin, StdInEmbeddedChannel):
    pass

class BlockingEmbeddedKernelManager(EmbeddedKernelManager):

    # The classes to use for the various channels.
    shell_channel_class = Type(BlockingShellEmbeddedChannel)
    sub_channel_class = Type(BlockingSubEmbeddedChannel)
    stdin_channel_class = Type(BlockingStdInEmbeddedChannel)
