"""Implement a fully blocking kernel manager.

Useful for test suites and blocking terminal interfaces.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
from Queue import Queue, Empty

# Our own
from IPython.utils import io
from IPython.utils.traitlets import Type

from .kernelmanager import (KernelManager, SubSocketChannel, 
                           XReqSocketChannel, RepSocketChannel, HBSocketChannel)

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

class BlockingSubSocketChannel(SubSocketChannel):

    def __init__(self, context, session, address=None):
        super(BlockingSubSocketChannel, self).__init__(context, session, address)
        self._in_queue = Queue()

    def call_handlers(self, msg):
        io.rprint('[[Sub]]', msg)  # dbg
        self._in_queue.put(msg)

    def msg_ready(self):
        """Is there a message that has been received?"""
        if self._in_queue.qsize() == 0:
            return False
        else:
            return True

    def get_msg(self, block=True, timeout=None):
        """Get a message if there is one that is ready."""
        return self._in_queue.get(block, timeout)

    def get_msgs(self):
        """Get all messages that are currently ready."""
        msgs = []
        while True:
            try:
                msgs.append(self.get_msg(block=False))
            except Empty:
                break
        return msgs

    

class BlockingXReqSocketChannel(XReqSocketChannel):

    def __init__(self, context, session, address=None):
        super(BlockingXReqSocketChannel, self).__init__(context, session, address)
        self._in_queue = Queue()

    def call_handlers(self, msg):
        io.rprint('[[XReq]]', msg)  # dbg

    def msg_ready(self):
        """Is there a message that has been received?"""
        if self._in_queue.qsize() == 0:
            return False
        else:
            return True

    def get_msg(self, block=True, timeout=None):
        """Get a message if there is one that is ready."""
        return self._in_queue.get(block, timeout)

    def get_msgs(self):
        """Get all messages that are currently ready."""
        msgs = []
        while True:
            try:
                msgs.append(self.get_msg(block=False))
            except Empty:
                break
        return msgs

class BlockingRepSocketChannel(RepSocketChannel):
    def call_handlers(self, msg):
        io.rprint('[[Rep]]', msg)  # dbg


class BlockingHBSocketChannel(HBSocketChannel):
    # This kernel needs rapid monitoring capabilities
    time_to_dead = 0.2

    def call_handlers(self, since_last_heartbeat):
        io.rprint('[[Heart]]', since_last_heartbeat) # dbg
    

class BlockingKernelManager(KernelManager):
    
    # The classes to use for the various channels.
    xreq_channel_class = Type(BlockingXReqSocketChannel)
    sub_channel_class = Type(BlockingSubSocketChannel)
    rep_channel_class = Type(BlockingRepSocketChannel)
    hb_channel_class = Type(BlockingHBSocketChannel)
  
