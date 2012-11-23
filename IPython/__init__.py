# encoding: utf-8
"""
IPython: tools for interactive and parallel computing in Python.

http://ipython.org
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import absolute_import

import os
import sys

#-----------------------------------------------------------------------------
# Setup everything
#-----------------------------------------------------------------------------

# Don't forget to also update setup.py when this changes!
if sys.version[0:3] < '2.6':
    raise ImportError('Python Version 2.6 or above is required for IPython.')

# Make it easy to import extensions - they are always directly on pythonpath.
# Therefore, non-IPython modules can be added to extensions directory.
# This should probably be in ipapp.py.
sys.path.append(os.path.join(os.path.dirname(__file__), "extensions"))

#-----------------------------------------------------------------------------
# Setup the top level names
#-----------------------------------------------------------------------------

from .config.loader import Config
from .core import release
from .core.application import Application
from .frontend.terminal.embed import embed

from .core.error import TryNext
from .core.interactiveshell import InteractiveShell
from .testing import test
from .utils.sysinfo import sys_info
from .utils.frame import extract_module_locals

# Release data
__author__ = ''
for author, email in release.authors.itervalues():
    __author__ += author + ' <' + email + '>\n'
__license__  = release.license
__version__  = release.version
version_info = release.version_info

def embed_kernel(module=None, local_ns=None, **kwargs):
    """Embed and start an IPython kernel in a given scope.
    
    Parameters
    ----------
    module : ModuleType, optional
        The module to load into IPython globals (default: caller)
    local_ns : dict, optional
        The namespace to load into IPython user namespace (default: caller)
    
    kwargs : various, optional
        Further keyword args are relayed to the KernelApp constructor,
        allowing configuration of the Kernel.  Will only have an effect
        on the first embed_kernel call for a given process.
    
    """
    
    (caller_module, caller_locals) = extract_module_locals(1)
    if module is None:
        module = caller_module
    if local_ns is None:
        local_ns = caller_locals
    
    # Only import .zmq when we really need it
    from .zmq.ipkernel import embed_kernel as real_embed_kernel
    real_embed_kernel(module=module, local_ns=local_ns, **kwargs)
