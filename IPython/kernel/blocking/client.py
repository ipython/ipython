"""Implements a fully blocking kernel client.

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

from IPython.utils.traitlets import Type
from IPython.kernel.client import KernelClient
from .channels import (
    BlockingIOPubChannel, BlockingHBChannel,
    BlockingShellChannel, BlockingStdInChannel
)

#-----------------------------------------------------------------------------
# Blocking kernel manager
#-----------------------------------------------------------------------------

class BlockingKernelClient(KernelClient):

    # The classes to use for the various channels
    shell_channel_class = Type(BlockingShellChannel)
    iopub_channel_class = Type(BlockingIOPubChannel)
    stdin_channel_class = Type(BlockingStdInChannel)
    hb_channel_class = Type(BlockingHBChannel)
