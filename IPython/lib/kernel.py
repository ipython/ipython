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
from getpass import getpass
from subprocess import Popen, PIPE

# external imports
from IPython.external.ssh import tunnel

# IPython imports
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

def tunnel_to_kernel(connection_info, sshserver, sshkey=None):
    """tunnel connections to a kernel via ssh
    
    This will open four SSH tunnels from localhost on this machine to the
    ports associated with the kernel.  They can be either direct
    localhost-localhost tunnels, or if an intermediate server is necessary,
    the kernel must be listening on a public IP.
    
    Parameters
    ----------
    connection_info : dict or str (path)
        Either a connection dict, or the path to a JSON connection file
    sshserver : str
        The ssh sever to use to tunnel to the kernel. Can be a full
        `user@server:port` string. ssh config aliases are respected.
    sshkey : str [optional]
        Path to file containing ssh key to use for authentication.
        Only necessary if your ssh config does not already associate
        a keyfile with the host.
    
    Returns
    -------
    
    (shell, iopub, stdin, hb) : ints
        The four ports on localhost that have been forwarded to the kernel.
    """
    if isinstance(connection_info, basestring):
        # it's a path, unpack it
        with open(connection_info) as f:
            connection_info = json.loads(f.read())
    
    cf = connection_info
    
    lports = tunnel.select_random_ports(4)
    rports = cf['shell_port'], cf['iopub_port'], cf['stdin_port'], cf['hb_port']
    
    remote_ip = cf['ip']
    
    if tunnel.try_passwordless_ssh(sshserver, sshkey):
        password=False
    else:
        password = getpass("SSH Password for %s: "%sshserver)
    
    for lp,rp in zip(lports, rports):
        tunnel.ssh_tunnel(lp, rp, sshserver, remote_ip, sshkey, password)
    
    return tuple(lports)
    

