"""Utilities for connecting to kernels

Authors:

* Min Ragan-Kelley

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import absolute_import

import glob
import json
import os
import socket
import sys
from getpass import getpass
from subprocess import Popen, PIPE
import tempfile

import zmq

# external imports
from IPython.external.ssh import tunnel

# IPython imports
# from IPython.config import Configurable
from IPython.core.profiledir import ProfileDir
from IPython.utils.localinterfaces import LOCALHOST
from IPython.utils.path import filefind, get_ipython_dir
from IPython.utils.py3compat import str_to_bytes, bytes_to_str
from IPython.utils.traitlets import (
    Bool, Integer, Unicode, CaselessStrEnum,
    HasTraits,
)


#-----------------------------------------------------------------------------
# Working with Connection Files
#-----------------------------------------------------------------------------

def write_connection_file(fname=None, shell_port=0, iopub_port=0, stdin_port=0, hb_port=0,
                         control_port=0, ip=LOCALHOST, key=b'', transport='tcp'):
    """Generates a JSON config file, including the selection of random ports.
    
    Parameters
    ----------

    fname : unicode
        The path to the file to write

    shell_port : int, optional
        The port to use for ROUTER channel.

    iopub_port : int, optional
        The port to use for the SUB channel.

    stdin_port : int, optional
        The port to use for the ROUTER (raw input) channel.

    control_port : int, optional
        The port to use for the ROUTER (raw input) channel.

    hb_port : int, optional
        The port to use for the hearbeat REP channel.

    ip  : str, optional
        The ip address the kernel will bind to.

    key : str, optional
        The Session key used for HMAC authentication.

    """
    # default to temporary connector file
    if not fname:
        fname = tempfile.mktemp('.json')
    
    # Find open ports as necessary.
    
    ports = []
    ports_needed = int(shell_port <= 0) + \
                   int(iopub_port <= 0) + \
                   int(stdin_port <= 0) + \
                   int(control_port <= 0) + \
                   int(hb_port <= 0)
    if transport == 'tcp':
        for i in range(ports_needed):
            sock = socket.socket()
            sock.bind(('', 0))
            ports.append(sock)
        for i, sock in enumerate(ports):
            port = sock.getsockname()[1]
            sock.close()
            ports[i] = port
    else:
        N = 1
        for i in range(ports_needed):
            while os.path.exists("%s-%s" % (ip, str(N))):
                N += 1
            ports.append(N)
            N += 1
    if shell_port <= 0:
        shell_port = ports.pop(0)
    if iopub_port <= 0:
        iopub_port = ports.pop(0)
    if stdin_port <= 0:
        stdin_port = ports.pop(0)
    if control_port <= 0:
        control_port = ports.pop(0)
    if hb_port <= 0:
        hb_port = ports.pop(0)
    
    cfg = dict( shell_port=shell_port,
                iopub_port=iopub_port,
                stdin_port=stdin_port,
                control_port=control_port,
                hb_port=hb_port,
              )
    cfg['ip'] = ip
    cfg['key'] = bytes_to_str(key)
    cfg['transport'] = transport
    
    with open(fname, 'w') as f:
        f.write(json.dumps(cfg, indent=2))
    
    return fname, cfg


def get_connection_file(app=None):
    """Return the path to the connection file of an app
    
    Parameters
    ----------
    app : IPKernelApp instance [optional]
        If unspecified, the currently running app will be used
    """
    if app is None:
        from IPython.kernel.zmq.kernelapp import IPKernelApp
        if not IPKernelApp.initialized():
            raise RuntimeError("app not specified, and not in a running Kernel")

        app = IPKernelApp.instance()
    return filefind(app.connection_file, ['.', app.profile_dir.security_dir])


def find_connection_file(filename, profile=None):
    """find a connection file, and return its absolute path.
    
    The current working directory and the profile's security
    directory will be searched for the file if it is not given by
    absolute path.
    
    If profile is unspecified, then the current running application's
    profile will be used, or 'default', if not run from IPython.
    
    If the argument does not match an existing file, it will be interpreted as a
    fileglob, and the matching file in the profile's security dir with
    the latest access time will be used.
    
    Parameters
    ----------
    filename : str
        The connection file or fileglob to search for.
    profile : str [optional]
        The name of the profile to use when searching for the connection file,
        if different from the current IPython session or 'default'.
    
    Returns
    -------
    str : The absolute path of the connection file.
    """
    from IPython.core.application import BaseIPythonApplication as IPApp
    try:
        # quick check for absolute path, before going through logic
        return filefind(filename)
    except IOError:
        pass
    
    if profile is None:
        # profile unspecified, check if running from an IPython app
        if IPApp.initialized():
            app = IPApp.instance()
            profile_dir = app.profile_dir
        else:
            # not running in IPython, use default profile
            profile_dir = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), 'default')
    else:
        # find profiledir by profile name:
        profile_dir = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile)
    security_dir = profile_dir.security_dir
    
    try:
        # first, try explicit name
        return filefind(filename, ['.', security_dir])
    except IOError:
        pass
    
    # not found by full name
    
    if '*' in filename:
        # given as a glob already
        pat = filename
    else:
        # accept any substring match
        pat = '*%s*' % filename
    matches = glob.glob( os.path.join(security_dir, pat) )
    if not matches:
        raise IOError("Could not find %r in %r" % (filename, security_dir))
    elif len(matches) == 1:
        return matches[0]
    else:
        # get most recent match, by access time:
        return sorted(matches, key=lambda f: os.stat(f).st_atime)[-1]


def get_connection_info(connection_file=None, unpack=False, profile=None):
    """Return the connection information for the current Kernel.
    
    Parameters
    ----------
    connection_file : str [optional]
        The connection file to be used. Can be given by absolute path, or
        IPython will search in the security directory of a given profile.
        If run from IPython, 
        
        If unspecified, the connection file for the currently running
        IPython Kernel will be used, which is only allowed from inside a kernel.
    unpack : bool [default: False]
        if True, return the unpacked dict, otherwise just the string contents
        of the file.
    profile : str [optional]
        The name of the profile to use when searching for the connection file,
        if different from the current IPython session or 'default'.
        
    
    Returns
    -------
    The connection dictionary of the current kernel, as string or dict,
    depending on `unpack`.
    """
    if connection_file is None:
        # get connection file from current kernel
        cf = get_connection_file()
    else:
        # connection file specified, allow shortnames:
        cf = find_connection_file(connection_file, profile=profile)
    
    with open(cf) as f:
        info = f.read()
    
    if unpack:
        info = json.loads(info)
        # ensure key is bytes:
        info['key'] = str_to_bytes(info.get('key', ''))
    return info


def connect_qtconsole(connection_file=None, argv=None, profile=None):
    """Connect a qtconsole to the current kernel.
    
    This is useful for connecting a second qtconsole to a kernel, or to a
    local notebook.
    
    Parameters
    ----------
    connection_file : str [optional]
        The connection file to be used. Can be given by absolute path, or
        IPython will search in the security directory of a given profile.
        If run from IPython, 
        
        If unspecified, the connection file for the currently running
        IPython Kernel will be used, which is only allowed from inside a kernel.
    argv : list [optional]
        Any extra args to be passed to the console.
    profile : str [optional]
        The name of the profile to use when searching for the connection file,
        if different from the current IPython session or 'default'.
    
    
    Returns
    -------
    subprocess.Popen instance running the qtconsole frontend
    """
    argv = [] if argv is None else argv
    
    if connection_file is None:
        # get connection file from current kernel
        cf = get_connection_file()
    else:
        cf = find_connection_file(connection_file, profile=profile)
    
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


#-----------------------------------------------------------------------------
# Mixin for classes that work with connection files
#-----------------------------------------------------------------------------

channel_socket_types = {
    'hb' : zmq.REQ,
    'shell' : zmq.DEALER,
    'iopub' : zmq.SUB,
    'stdin' : zmq.DEALER,
    'control': zmq.DEALER,
}

port_names = [ "%s_port" % channel for channel in ('shell', 'stdin', 'iopub', 'hb', 'control')]

class ConnectionFileMixin(HasTraits):
    """Mixin for configurable classes that work with connection files"""

    # The addresses for the communication channels
    connection_file = Unicode('')
    _connection_file_written = Bool(False)

    transport = CaselessStrEnum(['tcp', 'ipc'], default_value='tcp', config=True)

    ip = Unicode(LOCALHOST, config=True,
        help="""Set the kernel\'s IP address [default localhost].
        If the IP address is something other than localhost, then
        Consoles on other machines will be able to connect
        to the Kernel, so be careful!"""
    )

    def _ip_default(self):
        if self.transport == 'ipc':
            if self.connection_file:
                return os.path.splitext(self.connection_file)[0] + '-ipc'
            else:
                return 'kernel-ipc'
        else:
            return LOCALHOST

    def _ip_changed(self, name, old, new):
        if new == '*':
            self.ip = '0.0.0.0'

    # protected traits

    shell_port = Integer(0)
    iopub_port = Integer(0)
    stdin_port = Integer(0)
    control_port = Integer(0)
    hb_port = Integer(0)

    @property
    def ports(self):
        return [ getattr(self, name) for name in port_names ]

    #--------------------------------------------------------------------------
    # Connection and ipc file management
    #--------------------------------------------------------------------------

    def get_connection_info(self):
        """return the connection info as a dict"""
        return dict(
            transport=self.transport,
            ip=self.ip,
            shell_port=self.shell_port,
            iopub_port=self.iopub_port,
            stdin_port=self.stdin_port,
            hb_port=self.hb_port,
            control_port=self.control_port,
        )

    def cleanup_connection_file(self):
        """Cleanup connection file *if we wrote it*

        Will not raise if the connection file was already removed somehow.
        """
        if self._connection_file_written:
            # cleanup connection files on full shutdown of kernel we started
            self._connection_file_written = False
            try:
                os.remove(self.connection_file)
            except (IOError, OSError, AttributeError):
                pass

    def cleanup_ipc_files(self):
        """Cleanup ipc files if we wrote them."""
        if self.transport != 'ipc':
            return
        for port in self.ports:
            ipcfile = "%s-%i" % (self.ip, port)
            try:
                os.remove(ipcfile)
            except (IOError, OSError):
                pass

    def write_connection_file(self):
        """Write connection info to JSON dict in self.connection_file."""
        if self._connection_file_written:
            return

        self.connection_file, cfg = write_connection_file(self.connection_file,
            transport=self.transport, ip=self.ip, key=self.session.key,
            stdin_port=self.stdin_port, iopub_port=self.iopub_port,
            shell_port=self.shell_port, hb_port=self.hb_port,
            control_port=self.control_port,
        )
        # write_connection_file also sets default ports:
        for name in port_names:
            setattr(self, name, cfg[name])

        self._connection_file_written = True

    def load_connection_file(self):
        """Load connection info from JSON dict in self.connection_file."""
        with open(self.connection_file) as f:
            cfg = json.loads(f.read())

        self.transport = cfg.get('transport', 'tcp')
        self.ip = cfg['ip']
        for name in port_names:
            setattr(self, name, cfg[name])
        self.session.key = str_to_bytes(cfg['key'])

    #--------------------------------------------------------------------------
    # Creating connected sockets
    #--------------------------------------------------------------------------

    def _make_url(self, channel):
        """Make a ZeroMQ URL for a given channel."""
        transport = self.transport
        ip = self.ip
        port = getattr(self, '%s_port' % channel)

        if transport == 'tcp':
            return "tcp://%s:%i" % (ip, port)
        else:
            return "%s://%s-%s" % (transport, ip, port)

    def _create_connected_socket(self, channel, identity=None):
        """Create a zmq Socket and connect it to the kernel."""
        url = self._make_url(channel)
        socket_type = channel_socket_types[channel]
        self.log.info("Connecting to: %s" % url)
        sock = self.context.socket(socket_type)
        if identity:
            sock.identity = identity
        sock.connect(url)
        return sock

    def connect_iopub(self, identity=None):
        """return zmq Socket connected to the IOPub channel"""
        sock = self._create_connected_socket('iopub', identity=identity)
        sock.setsockopt(zmq.SUBSCRIBE, b'')
        return sock

    def connect_shell(self, identity=None):
        """return zmq Socket connected to the Shell channel"""
        return self._create_connected_socket('shell', identity=identity)

    def connect_stdin(self, identity=None):
        """return zmq Socket connected to the StdIn channel"""
        return self._create_connected_socket('stdin', identity=identity)

    def connect_hb(self, identity=None):
        """return zmq Socket connected to the Heartbeat channel"""
        return self._create_connected_socket('hb', identity=identity)

    def connect_control(self, identity=None):
        """return zmq Socket connected to the Heartbeat channel"""
        return self._create_connected_socket('control', identity=identity)


__all__ = [
    'write_connection_file',
    'get_connection_file',
    'find_connection_file',
    'get_connection_info',
    'connect_qtconsole',
    'tunnel_to_kernel',
]
