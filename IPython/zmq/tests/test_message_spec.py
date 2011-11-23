"""Test suite for our zeromq-based messaging specification.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import time

import nose.tools as nt

from ..blockingkernelmanager import BlockingKernelManager

from IPython.utils import io

def setup():
    global KM
    KM = BlockingKernelManager()

    KM.start_kernel()
    KM.start_channels()
    # Give the kernel a chance to come up.
    time.sleep(1)

def teardown():
    io.rprint('Entering teardown...')  # dbg
    io.rprint('Stopping channels and kernel...')  # dbg
    KM.stop_channels()
    KM.kill_kernel()


# Actual tests

def test_execute():
    KM.shell_channel.execute(code='x=1')
    KM.shell_channel.execute(code='print 1')
    
