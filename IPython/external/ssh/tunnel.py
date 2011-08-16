"""Basic ssh tunneling utilities."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------



#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function

import os,sys, atexit
from multiprocessing import Process
from getpass import getpass, getuser
import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        import paramiko
except ImportError:
    paramiko = None
else:
    from forward import forward_tunnel

try:
    from IPython.external import pexpect
except ImportError:
    pexpect = None

from IPython.parallel.util import select_random_ports

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Check for passwordless login
#-----------------------------------------------------------------------------

def try_passwordless_ssh(server, keyfile, paramiko=None):
    """Attempt to make an ssh connection without a password.
    This is mainly used for requiring password input only once
    when many tunnels may be connected to the same server.
    
    If paramiko is None, the default for the platform is chosen.
    """
    if paramiko is None:
        paramiko = sys.platform == 'win32'
    if not paramiko:
        f = _try_passwordless_openssh
    else:
        f = _try_passwordless_paramiko
    return f(server, keyfile)

def _try_passwordless_openssh(server, keyfile):
    """Try passwordless login with shell ssh command."""
    if pexpect is None:
        raise ImportError("pexpect unavailable, use paramiko")
    cmd = 'ssh -f '+ server
    if keyfile:
        cmd += ' -i ' + keyfile
    cmd += ' exit'
    p = pexpect.spawn(cmd)
    while True:
        try:
            p.expect('[Ppassword]:', timeout=.1)
        except pexpect.TIMEOUT:
            continue
        except pexpect.EOF:
            return True
        else:
            return False

def _try_passwordless_paramiko(server, keyfile):
    """Try passwordless login with paramiko."""
    if paramiko is None:
        msg = "Paramiko unavaliable, "
        if sys.platform == 'win32':
            msg += "Paramiko is required for ssh tunneled connections on Windows."
        else:
            msg += "use OpenSSH."
        raise ImportError(msg)
    username, server, port = _split_server(server)
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    try:
        client.connect(server, port, username=username, key_filename=keyfile,
               look_for_keys=True)
    except paramiko.AuthenticationException:
        return False
    else:
        client.close()
        return True


def tunnel_connection(socket, addr, server, keyfile=None, password=None, paramiko=None):
    """Connect a socket to an address via an ssh tunnel.
    
    This is a wrapper for socket.connect(addr), when addr is not accessible
    from the local machine.  It simply creates an ssh tunnel using the remaining args,
    and calls socket.connect('tcp://localhost:lport') where lport is the randomly
    selected local port of the tunnel.
    
    """
    new_url, tunnel = open_tunnel(addr, server, keyfile=keyfile, password=password, paramiko=paramiko)
    socket.connect(new_url)
    return tunnel


def open_tunnel(addr, server, keyfile=None, password=None, paramiko=None):
    """Open a tunneled connection from a 0MQ url.
    
    For use inside tunnel_connection.
    
    Returns
    -------
    
    (url, tunnel): The 0MQ url that has been forwarded, and the tunnel object
    """
    
    lport = select_random_ports(1)[0]
    transport, addr = addr.split('://')
    ip,rport = addr.split(':')
    rport = int(rport)
    if paramiko is None:
        paramiko = sys.platform == 'win32'
    if paramiko:
        tunnelf = paramiko_tunnel
    else:
        tunnelf = openssh_tunnel
    tunnel = tunnelf(lport, rport, server, remoteip=ip, keyfile=keyfile, password=password)
    return 'tcp://127.0.0.1:%i'%lport, tunnel

def openssh_tunnel(lport, rport, server, remoteip='127.0.0.1', keyfile=None, password=None, timeout=15):
    """Create an ssh tunnel using command-line ssh that connects port lport
    on this machine to localhost:rport on server.  The tunnel
    will automatically close when not in use, remaining open
    for a minimum of timeout seconds for an initial connection.
    
    This creates a tunnel redirecting `localhost:lport` to `remoteip:rport`,
    as seen from `server`.
    
    keyfile and password may be specified, but ssh config is checked for defaults.
    
    Parameters
    ----------
    
        lport : int
            local port for connecting to the tunnel from this machine.
        rport : int
            port on the remote machine to connect to.
        server : str
            The ssh server to connect to. The full ssh server string will be parsed.
            user@server:port
        remoteip : str [Default: 127.0.0.1]
            The remote ip, specifying the destination of the tunnel.
            Default is localhost, which means that the tunnel would redirect
            localhost:lport on this machine to localhost:rport on the *server*.
        
        keyfile : str; path to public key file
            This specifies a key to be used in ssh login, default None.
            Regular default ssh keys will be used without specifying this argument.
        password : str; 
            Your ssh password to the ssh server. Note that if this is left None,
            you will be prompted for it if passwordless key based login is unavailable.
    
    """
    if pexpect is None:
        raise ImportError("pexpect unavailable, use paramiko_tunnel")
    ssh="ssh "
    if keyfile:
        ssh += "-i " + keyfile 
    cmd = ssh + " -f -L 127.0.0.1:%i:%s:%i %s sleep %i"%(lport, remoteip, rport, server, timeout)
    tunnel = pexpect.spawn(cmd)
    failed = False
    while True:
        try:
            tunnel.expect('[Pp]assword:', timeout=.1)
        except pexpect.TIMEOUT:
            continue
        except pexpect.EOF:
            if tunnel.exitstatus:
                print (tunnel.exitstatus)
                print (tunnel.before)
                print (tunnel.after)
                raise RuntimeError("tunnel '%s' failed to start"%(cmd))
            else:
                return tunnel.pid
        else:
            if failed:
                print("Password rejected, try again")
                password=None
            if password is None:
                password = getpass("%s's password: "%(server))
            tunnel.sendline(password)
            failed = True
    
def _split_server(server):
    if '@' in server:
        username,server = server.split('@', 1)
    else:
        username = getuser()
    if ':' in server:
        server, port = server.split(':')
        port = int(port)
    else:
        port = 22
    return username, server, port

def paramiko_tunnel(lport, rport, server, remoteip='127.0.0.1', keyfile=None, password=None, timeout=15):
    """launch a tunner with paramiko in a subprocess. This should only be used
    when shell ssh is unavailable (e.g. Windows).
    
    This creates a tunnel redirecting `localhost:lport` to `remoteip:rport`,
    as seen from `server`.
    
    If you are familiar with ssh tunnels, this creates the tunnel:
    
    ssh server -L localhost:lport:remoteip:rport
    
    keyfile and password may be specified, but ssh config is checked for defaults.
    
    
    Parameters
    ----------
    
        lport : int
            local port for connecting to the tunnel from this machine.
        rport : int
            port on the remote machine to connect to.
        server : str
            The ssh server to connect to. The full ssh server string will be parsed.
            user@server:port
        remoteip : str [Default: 127.0.0.1]
            The remote ip, specifying the destination of the tunnel.
            Default is localhost, which means that the tunnel would redirect
            localhost:lport on this machine to localhost:rport on the *server*.
        
        keyfile : str; path to public key file
            This specifies a key to be used in ssh login, default None.
            Regular default ssh keys will be used without specifying this argument.
        password : str; 
            Your ssh password to the ssh server. Note that if this is left None,
            you will be prompted for it if passwordless key based login is unavailable.
    
    """
    if paramiko is None:
        raise ImportError("Paramiko not available")
    
    if password is None:
        if not _check_passwordless_paramiko(server, keyfile):
            password = getpass("%s's password: "%(server))

    p = Process(target=_paramiko_tunnel, 
            args=(lport, rport, server, remoteip), 
            kwargs=dict(keyfile=keyfile, password=password))
    p.daemon=False
    p.start()
    atexit.register(_shutdown_process, p)
    return p
    
def _shutdown_process(p):
    if p.isalive():
        p.terminate()

def _paramiko_tunnel(lport, rport, server, remoteip, keyfile=None, password=None):
    """Function for actually starting a paramiko tunnel, to be passed
    to multiprocessing.Process(target=this), and not called directly.
    """
    username, server, port = _split_server(server)
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        client.connect(server, port, username=username, key_filename=keyfile,
                       look_for_keys=True, password=password)
#    except paramiko.AuthenticationException:
#        if password is None:
#            password = getpass("%s@%s's password: "%(username, server))
#            client.connect(server, port, username=username, password=password)
#        else:
#            raise
    except Exception as e:
        print ('*** Failed to connect to %s:%d: %r' % (server, port, e))
        sys.exit(1)

    # print ('Now forwarding port %d to %s:%d ...' % (lport, server, rport))

    try:
        forward_tunnel(lport, remoteip, rport, client.get_transport())
    except KeyboardInterrupt:
        print ('SIGINT: Port forwarding stopped cleanly')
        sys.exit(0)
    except Exception as e:
        print ("Port forwarding stopped uncleanly: %s"%e)
        sys.exit(255)

if sys.platform == 'win32':
    ssh_tunnel = paramiko_tunnel
else:
    ssh_tunnel = openssh_tunnel

    
__all__ = ['tunnel_connection', 'ssh_tunnel', 'openssh_tunnel', 'paramiko_tunnel', 'try_passwordless_ssh']


