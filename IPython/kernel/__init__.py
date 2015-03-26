"""IPython kernels and associated utilities

For connecting to kernels, use jupyter_client
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# Shim to maintain backwards compatibility with old IPython.kernel imports.

import sys
from warnings import warn

warn("The `IPython.kernel` package has been deprecated. "
     "You should import from ipython_kernel or jupyter_client instead.")

from IPython.utils.shimmodule import ShimModule

# Shims for jupyter_client
# Can't do a single shim, because the package didn't move all together

for name in (
    'adapter',
    'blocking',
    'channels',
    'channelsabc',
    'client',
    'clientabc',
    'connect',
    'ioloop',
    'kernelspec',
    'kernelspecapp',
    'launcher',
    'manager',
    'managerabc',
    'multikernelmanager',
    'restarter',
    'threaded',
    'tests.test_adapter',
    'tests.test_connect',
    'tests.test_kernelmanager',
    'tests.test_kernelspec',
    'tests.test_launcher',
    'tests.test_multikernelmanager',
    'tests.test_public_api',
):
    sys.modules['IPython.kernel.%s' % name] = \
        ShimModule(name, mirror='jupyter_client.%s' % name)

# some files moved out of the zmq prefix
for name in (
    'session',
    'tests.test_session',
):
    sys.modules['IPython.kernel.zmq.%s' % name] = \
        ShimModule(name, mirror='jupyter_client.%s' % name)
# preserve top-level API modules, all from jupyter_client

# just for friendlier zmq version check
from . import zmq

from jupyter_client.connect import *
from jupyter_client.launcher import *
from jupyter_client.client import KernelClient
from jupyter_client.manager import KernelManager, run_kernel
from jupyter_client.blocking import BlockingKernelClient
from jupyter_client.multikernelmanager import MultiKernelManager

