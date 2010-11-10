

#-----------------------------------------
# Imports
#-----------------------------------------

from __future__ import print_function

import os,sys
from multiprocessing import Process
from getpass import getpass, getuser

try:
    import paramiko
except ImportError:
    paramiko = None
else:
    from forward import forward_tunnel
    
from IPython.external import pexpect


def launch_ssh_tunnel(lport, rport, server, remoteip='127.0.0.1', keyfile=None, timeout=15):
    """Create an ssh tunnel using command-line ssh that connects port lport
    on this machine to localhost:rport on server.  The tunnel
    will automatically close when not in use, remaining open
    for a minimum of timeout seconds for an initial connection.
    """
    ssh="ssh "
    if keyfile:
        ssh += "-i " + keyfile 
    cmd = ssh + " -f -L %i:127.0.0.1:%i %s sleep %i"%(lport, rport, server, timeout)
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
            tunnel.sendline(getpass())
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

def launch_paramiko_tunnel(lport, rport, server, remoteip='127.0.0.1', keyfile=None):
    """launch a tunner with paramiko in a subprocess"""
    if paramiko is None:
        raise ImportError("Paramiko not available")
    server = _split_server(server)
    if keyfile is None:
        passwd = getpass("%s@%s's password: "%(server[0], server[1]))
    else:
        passwd = None
    p = Process(target=_paramiko_tunnel, 
            args=(lport, rport, server, remoteip), 
            kwargs=dict(keyfile=keyfile, password=passwd))
    p.daemon=False
    p.start()
    return p
    

def _paramiko_tunnel(lport, rport, server, remoteip, keyfile=None, password=None):
    """function for actually starting a paramiko tunnel, to be passed
    to multiprocessing.Process(target=this).
    """
    username, server, port = server
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        client.connect(server, port, username=username, key_filename=keyfile,
                       look_for_keys=True, password=password)
    except Exception as e:
        print ('*** Failed to connect to %s:%d: %r' % (server, port, e))
        sys.exit(1)

    print ('Now forwarding port %d to %s:%d ...' % (lport, server, rport))

    try:
        forward_tunnel(lport, remoteip, rport, client.get_transport())
    except KeyboardInterrupt:
        print ('C-c: Port forwarding stopped.')
        sys.exit(0)

    
__all__ = ['launch_ssh_tunnel', 'launch_paramiko_tunnel']















