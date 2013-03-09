"""Blocking channels

Useful for test suites and blocking terminal interfaces.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import Queue

from IPython.kernel.channels import IOPubChannel, HBChannel, \
    ShellChannel, StdInChannel

#-----------------------------------------------------------------------------
# Blocking kernel manager
#-----------------------------------------------------------------------------


class BlockingChannelMixin(object):

    def __init__(self, *args, **kwds):
        super(BlockingChannelMixin, self).__init__(*args, **kwds)
        self._in_queue = Queue.Queue()

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
            except Queue.Empty:
                break
        return msgs

    def msg_ready(self):
        """ Is there a message that has been received? """
        return not self._in_queue.empty()


class BlockingIOPubChannel(BlockingChannelMixin, IOPubChannel):
    pass


class BlockingShellChannel(BlockingChannelMixin, ShellChannel):
    pass


class BlockingStdInChannel(BlockingChannelMixin, StdInChannel):
    pass


class BlockingHBChannel(HBChannel):

    # This kernel needs quicker monitoring, shorten to 1 sec.
    # less than 0.5s is unreliable, and will get occasional
    # false reports of missed beats.
    time_to_dead = 1.

    def call_handlers(self, since_last_heartbeat):
        """ Pause beating on missed heartbeat. """
        pass
