"""Utilities for connecting to kernels

Authors:

* Min Ragan-Kelley

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json
import sys
from subprocess import Popen, PIPE

from IPython.utils.path import filefind
from IPython.utils.py3compat import str_to_bytes


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def get_connection_file(app=None):
    """Return the path to the connection file of an app
    
    Parameters
    ----------
    app : KernelApp instance [optional]
        If unspecified, the currently running app will be used
    """
    if app is None:
        from IPython.zmq.kernelapp import KernelApp
        if not KernelApp.initialized():
            raise RuntimeError("app not specified, and not in a running Kernel")

        app = KernelApp.instance()
    return filefind(app.connection_file, ['.', app.profile_dir.security_dir])
        
def get_connection_info(unpack=False):
    """Return the connection information for the current Kernel.
    
    Parameters
    ----------
    unpack : bool [default: False]
        if True, return the unpacked dict, otherwise just the string contents
        of the file.
    
    Returns
    -------
    The connection dictionary of the current kernel, as string or dict,
    depending on `unpack`.
    """
    cf = get_connection_file()
    with open(cf) as f:
        info = f.read()
    
    if unpack:
        info = json.loads(info)
        # ensure key is bytes:
        info['key'] = str_to_bytes(info.get('key', ''))
    return info

def connect_qtconsole(argv=None):
    """Connect a qtconsole to the current kernel.
    
    This is useful for connecting a second qtconsole to a kernel, or to a
    local notebook.
    
    Parameters
    ----------
    argv : list [optional]
        Any extra args to be passed to the console.
    
    Returns
    -------
    subprocess.Popen instance running the qtconsole frontend
    """
    argv = [] if argv is None else argv
    
    # get connection file from current kernel
    cf = get_connection_file()
    
    cmd = ';'.join([
        "from IPython.frontend.qt.console import qtconsoleapp",
        "qtconsoleapp.main()"
    ])
    
    return Popen([sys.executable, '-c', cmd, '--existing', cf] + argv, stdout=PIPE, stderr=PIPE)


