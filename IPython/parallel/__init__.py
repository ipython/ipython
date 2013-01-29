"""The IPython ZMQ-based parallel computing interface.

Authors:

* MinRK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import warnings

import zmq

from IPython.config.configurable import MultipleInstanceError
from IPython.zmq import check_for_zmq

min_pyzmq = '2.1.11'

check_for_zmq(min_pyzmq, 'IPython.parallel')

from IPython.utils.pickleutil import Reference

from .client.asyncresult import *
from .client.client import Client
from .client.remotefunction import *
from .client.view import *
from .controller.dependency import *
from .error import *
from .util import interactive

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------


def bind_kernel(**kwargs):
    """Bind an Engine's Kernel to be used as a full IPython kernel.
    
    This allows a running Engine to be used simultaneously as a full IPython kernel
    with the QtConsole or other frontends.
    
    This function returns immediately.
    """
    from IPython.zmq.ipkernel import IPKernelApp
    from IPython.parallel.apps.ipengineapp import IPEngineApp
    
    # first check for IPKernelApp, in which case this should be a no-op
    # because there is already a bound kernel
    if IPKernelApp.initialized() and isinstance(IPKernelApp._instance, IPKernelApp):
        return
    
    if IPEngineApp.initialized():
        try:
            app = IPEngineApp.instance()
        except MultipleInstanceError:
            pass
        else:
            return app.bind_kernel(**kwargs)
    
    raise RuntimeError("bind_kernel be called from an IPEngineApp instance")
    


