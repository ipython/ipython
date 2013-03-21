"""Utilities for launching kernels

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

import os
import sys
from subprocess import Popen, PIPE

from IPython.utils.py3compat import cast_bytes_py2

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
        
        if cwd:
            # Popen on Python 2 on Windows cannot handle unicode cwd.
            cwd = cast_bytes_py2(cwd, sys.getfilesystemencoding() or 'ascii')
        
        from IPython.kernel.zmq.parentpoller import ParentPollerWindows
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
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, env=os.environ)
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
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd, env=os.environ)

        # Attach the interrupt event to the Popen objet so it can be used later.
        proc.win32_interrupt_event = interrupt_event

    else:
        if independent:
            proc = Popen(cmd, preexec_fn=lambda: os.setsid(),
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd, env=os.environ)
        else:
            if ipython_kernel:
                cmd += ['--parent=1']
            proc = Popen(cmd,
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd, env=os.environ)

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

__all__ = [
    'swallow_argv',
    'make_ipkernel_cmd',
    'launch_kernel',
]
