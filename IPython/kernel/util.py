"""Utilities for working with kernels and their connection files

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

import glob
import json
import os
import socket
import sys
from getpass import getpass
from subprocess import Popen, PIPE
import tempfile

# external imports
from IPython.external.ssh import tunnel

# IPython imports
from IPython.core.profiledir import ProfileDir
from IPython.utils.localinterfaces import LOCALHOST
from IPython.utils.path import filefind, get_ipython_dir
from IPython.utils.py3compat import str_to_bytes, bytes_to_str


#-----------------------------------------------------------------------------
# Working with Connection Files
#-----------------------------------------------------------------------------

def write_connection_file(fname=None, shell_port=0, iopub_port=0, stdin_port=0, hb_port=0,
                         ip=LOCALHOST, key=b'', transport='tcp'):
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
        The port to use for the REQ (raw input) channel.

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
    ports_needed = int(shell_port <= 0) + int(iopub_port <= 0) + \
                   int(stdin_port <= 0) + int(hb_port <= 0)
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
    if hb_port <= 0:
        hb_port = ports.pop(0)
    
    cfg = dict( shell_port=shell_port,
                iopub_port=iopub_port,
                stdin_port=stdin_port,
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
    app : KernelApp instance [optional]
        If unspecified, the currently running app will be used
    """
    if app is None:
        from IPython.zmq.ipkernel import IPKernelApp
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
# Launching Kernels
#-----------------------------------------------------------------------------

def swallow_argv(argv, aliases=None, flags=None):
    """strip frontend-specific aliases and flags from an argument list
    
    For use primarily in frontend apps that want to pass a subset of command-line
    arguments through to a subprocess, where frontend-specific flags and aliases
    should be removed from the list.
    
    Parameters
    ----------
    
    argv : list(str)
        The starting argv, to be filtered
    aliases : container of aliases (dict, list, set, etc.)
        The frontend-specific aliases to be removed
    flags : container of flags (dict, list, set, etc.)
        The frontend-specific flags to be removed
    
    Returns
    -------
    
    argv : list(str)
        The argv list, excluding flags and aliases that have been stripped
    """
    
    if aliases is None:
        aliases = set()
    if flags is None:
        flags = set()
    
    stripped = list(argv) # copy
    
    swallow_next = False
    was_flag = False
    for a in argv:
        if swallow_next:
            swallow_next = False
            # last arg was an alias, remove the next one
            # *unless* the last alias has a no-arg flag version, in which
            # case, don't swallow the next arg if it's also a flag:
            if not (was_flag and a.startswith('-')):
                stripped.remove(a)
                continue
        if a.startswith('-'):
            split = a.lstrip('-').split('=')
            alias = split[0]
            if alias in aliases:
                stripped.remove(a)
                if len(split) == 1:
                    # alias passed with arg via space
                    swallow_next = True
                    # could have been a flag that matches an alias, e.g. `existing`
                    # in which case, we might not swallow the next arg
                    was_flag = alias in flags
            elif alias in flags and len(split) == 1:
                # strip flag, but don't swallow next, as flags don't take args
                stripped.remove(a)
    
    # return shortened list
    return stripped


def make_ipkernel_cmd(code, executable=None, extra_arguments=[], **kw):
    """Build Popen command list for launching an IPython kernel.

    Parameters
    ----------
    code : str,
        A string of Python code that imports and executes a kernel entry point.

    executable : str, optional (default sys.executable)
        The Python executable to use for the kernel process.

    extra_arguments : list, optional
        A list of extra arguments to pass when executing the launch code.
    
    Returns
    -------
    
    A Popen command list
    """
    
    # Build the kernel launch command.
    if executable is None:
        executable = sys.executable
    arguments = [ executable, '-c', code, '-f', '{connection_file}' ]
    arguments.extend(extra_arguments)

    # Spawn a kernel.
    if sys.platform == 'win32':

        # If the kernel is running on pythonw and stdout/stderr are not been
        # re-directed, it will crash when more than 4KB of data is written to
        # stdout or stderr. This is a bug that has been with Python for a very
        # long time; see http://bugs.python.org/issue706263.
        # A cleaner solution to this problem would be to pass os.devnull to
        # Popen directly. Unfortunately, that does not work.
        if executable.endswith('pythonw.exe'):
            arguments.append('--no-stdout')
            arguments.append('--no-stderr')

    return arguments


def launch_kernel(cmd, stdin=None, stdout=None, stderr=None,
                        independent=False,
                        cwd=None, ipython_kernel=True,
                        **kw
                        ):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    cmd : Popen list,
        A string of Python code that imports and executes a kernel entry point.

    stdin, stdout, stderr : optional (default None)
        Standards streams, as defined in subprocess.Popen.

    independent : bool, optional (default False)
        If set, the kernel process is guaranteed to survive if this process
        dies. If not set, an effort is made to ensure that the kernel is killed
        when this process dies. Note that in this case it is still good practice
        to kill kernels manually before exiting.

    cwd : path, optional
        The working dir of the kernel process (default: cwd of this process).

    ipython_kernel : bool, optional
        Whether the kernel is an official IPython one,
        and should get a bit of special treatment.

    Returns
    -------
    
    Popen instance for the kernel subprocess
    """

    # Popen will fail (sometimes with a deadlock) if stdin, stdout, and stderr
    # are invalid. Unfortunately, there is in general no way to detect whether
    # they are valid.  The following two blocks redirect them to (temporary)
    # pipes in certain important cases.

    # If this process has been backgrounded, our stdin is invalid. Since there
    # is no compelling reason for the kernel to inherit our stdin anyway, we'll
    # place this one safe and always redirect.
    redirect_in = True
    _stdin = PIPE if stdin is None else stdin

    # If this process in running on pythonw, we know that stdin, stdout, and
    # stderr are all invalid.
    redirect_out = sys.executable.endswith('pythonw.exe')
    if redirect_out:
        _stdout = PIPE if stdout is None else stdout
        _stderr = PIPE if stderr is None else stderr
    else:
        _stdout, _stderr = stdout, stderr

    # Spawn a kernel.
    if sys.platform == 'win32':
        from IPython.zmq.parentpoller import ParentPollerWindows
        # Create a Win32 event for interrupting the kernel.
        interrupt_event = ParentPollerWindows.create_interrupt_event()
        if ipython_kernel:
            cmd += [ '--interrupt=%i' % interrupt_event ]

            # If the kernel is running on pythonw and stdout/stderr are not been
            # re-directed, it will crash when more than 4KB of data is written to
            # stdout or stderr. This is a bug that has been with Python for a very
            # long time; see http://bugs.python.org/issue706263.
            # A cleaner solution to this problem would be to pass os.devnull to
            # Popen directly. Unfortunately, that does not work.
            if cmd[0].endswith('pythonw.exe'):
                if stdout is None:
                    cmd.append('--no-stdout')
                if stderr is None:
                    cmd.append('--no-stderr')

        # Launch the kernel process.
        if independent:
            proc = Popen(cmd,
                         creationflags=512, # CREATE_NEW_PROCESS_GROUP
                         stdin=_stdin, stdout=_stdout, stderr=_stderr)
        else:
            if ipython_kernel:
                try:
                    from _winapi import DuplicateHandle, GetCurrentProcess, \
                        DUPLICATE_SAME_ACCESS
                except:
                    from _subprocess import DuplicateHandle, GetCurrentProcess, \
                        DUPLICATE_SAME_ACCESS
                pid = GetCurrentProcess()
                handle = DuplicateHandle(pid, pid, pid, 0,
                                         True, # Inheritable by new processes.
                                         DUPLICATE_SAME_ACCESS)
                cmd +=[ '--parent=%i' % handle ]
            
            
            proc = Popen(cmd,
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd)

        # Attach the interrupt event to the Popen objet so it can be used later.
        proc.win32_interrupt_event = interrupt_event

    else:
        if independent:
            proc = Popen(cmd, preexec_fn=lambda: os.setsid(),
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd)
        else:
            if ipython_kernel:
                cmd += ['--parent=1']
            proc = Popen(cmd,
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd)

    # Clean up pipes created to work around Popen bug.
    if redirect_in:
        if stdin is None:
            proc.stdin.close()
    if redirect_out:
        if stdout is None:
            proc.stdout.close()
        if stderr is None:
            proc.stderr.close()

    return proc

