"""
Shim to maintain backwards compatibility with old IPython.kernel imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.kernel` package has been deprecated. "
     "You should import from ipython_kernel or jupyter_client instead.")


from IPython.utils.shimmodule import ShimModule

# zmq subdir is gone
sys.modules['IPython.kernel.zmq.session'] = ShimModule(
    src='IPython.kernel.zmq.session', mirror='jupyter_client.session')
sys.modules['IPython.kernel.zmq'] = ShimModule(
    src='IPython.kernel.zmq', mirror='ipython_kernel')

for pkg in ('comm', 'inprocess'):
    src = 'IPython.kernel.%s' % pkg
    sys.modules[src] = ShimModule(src=src, mirror='ipython_kernel.%s' % pkg)

for pkg in ('ioloop', 'blocking'):
    src = 'IPython.kernel.%s' % pkg
    sys.modules[src] = ShimModule(src=src, mirror='jupyter_client.%s' % pkg)

# required for `from IPython.kernel import PKG`
from ipython_kernel import comm, inprocess
from jupyter_client import ioloop, blocking
# public API
from ipython_kernel.connect import *
from jupyter_client import *
