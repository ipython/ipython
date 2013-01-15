""" Implements a fully blocking kernel manager.

Useful for test suites and blocking terminal interfaces.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Local imports.
from IPython.inprocess.blockingkernelmanager import BlockingChannelMixin
from IPython.utils.traitlets import Type
from kernelmanager import KernelManager, SubSocketChannel, HBSocketChannel, \
    ShellSocketChannel, StdInSocketChannel

#-----------------------------------------------------------------------------
# Blocking kernel manager
#-----------------------------------------------------------------------------

class BlockingSubSocketChannel(BlockingChannelMixin, SubSocketChannel):
    pass

class BlockingShellSocketChannel(BlockingChannelMixin, ShellSocketChannel):
    pass

class BlockingStdInSocketChannel(BlockingChannelMixin, StdInSocketChannel):
    pass

class BlockingHBSocketChannel(HBSocketChannel):
    
    # This kernel needs quicker monitoring, shorten to 1 sec.
    # less than 0.5s is unreliable, and will get occasional
    # false reports of missed beats.
    time_to_dead = 1.

    def call_handlers(self, since_last_heartbeat):
        """ Pause beating on missed heartbeat. """
        pass

class BlockingKernelManager(KernelManager):
    
    # The classes to use for the various channels.
    shell_channel_class = Type(BlockingShellSocketChannel)
    sub_channel_class = Type(BlockingSubSocketChannel)
    stdin_channel_class = Type(BlockingStdInSocketChannel)
    hb_channel_class = Type(BlockingHBSocketChannel)
  
