"""Utilities for launching kernels
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys
from subprocess import Popen, PIPE

from IPython.utils.encoding import getdefaultencoding
from IPython.utils.py3compat import cast_bytes_py2


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
        if a == '--':
            break
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
            name = split[0]
            # we use startswith because argparse accepts any arg to be specified
            # by any leading section, as long as it is unique,
            # so `--no-br` means `--no-browser` in the notebook, etc.
            if any(alias.startswith(name) for alias in aliases):
                stripped.remove(a)
                if len(split) == 1:
                    # alias passed with arg via space
                    swallow_next = True
                    # could have been a flag that matches an alias, e.g. `existing`
                    # in which case, we might not swallow the next arg
                    was_flag = name in flags
            elif len(split) == 1 and any(flag.startswith(name) for flag in flags):
                # strip flag, but don't swallow next, as flags don't take args
                stripped.remove(a)
    
    # return shortened list
    return stripped


def make_ipkernel_cmd(mod='IPython.kernel', executable=None, extra_arguments=[], **kw):
    """Build Popen command list for launching an IPython kernel.

    Parameters
    ----------
    mod : str, optional (default 'IPython.kernel')
        A string of an IPython module whose __main__ starts an IPython kernel

    executable : str, optional (default sys.executable)
        The Python executable to use for the kernel process.

    extra_arguments : list, optional
        A list of extra arguments to pass when executing the launch code.
    
    Returns
    -------
    
    A Popen command list
    """
    if executable is None:
        executable = sys.executable
    arguments = [ executable, '-m', mod, '-f', '{connection_file}' ]
    arguments.extend(extra_arguments)
    
    return arguments


def launch_kernel(cmd, stdin=None, stdout=None, stderr=None, env=None,
                        independent=False,
                        cwd=None,
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
        blackhole = open(os.devnull, 'w')
        _stdout = blackhole if stdout is None else stdout
        _stderr = blackhole if stderr is None else stderr
    else:
        _stdout, _stderr = stdout, stderr
    
    env = env if (env is not None) else os.environ.copy()

    encoding = getdefaultencoding(prefer_stream=False)
    kwargs = dict(
        stdin=_stdin,
        stdout=_stdout,
        stderr=_stderr,
        cwd=cwd,
        env=env,
    )
    
    # Spawn a kernel.
    if sys.platform == 'win32':
        # Popen on Python 2 on Windows cannot handle unicode args or cwd
        cmd = [ cast_bytes_py2(c, encoding) for c in cmd ]
        if cwd:
            cwd = cast_bytes_py2(cwd, sys.getfilesystemencoding() or 'ascii')
            kwargs['cwd'] = cwd
        
        from IPython.kernel.zmq.parentpoller import ParentPollerWindows
        # Create a Win32 event for interrupting the kernel
        # and store it in an environment variable.
        interrupt_event = ParentPollerWindows.create_interrupt_event()
        env["JPY_INTERRUPT_EVENT"] = str(interrupt_event)
        # deprecated old env name:
        env["IPY_INTERRUPT_EVENT"] = env["JPY_INTERRUPT_EVENT"]

        try:
            from _winapi import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS, CREATE_NEW_PROCESS_GROUP
        except:
            from _subprocess import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS, CREATE_NEW_PROCESS_GROUP
        # Launch the kernel process
        if independent:
            kwargs['creationflags'] = CREATE_NEW_PROCESS_GROUP
        else:
            pid = GetCurrentProcess()
            handle = DuplicateHandle(pid, pid, pid, 0,
                                     True, # Inheritable by new processes.
                                     DUPLICATE_SAME_ACCESS)
            env['JPY_PARENT_PID'] = str(int(handle))
        
        proc = Popen(cmd, **kwargs)

        # Attach the interrupt event to the Popen objet so it can be used later.
        proc.win32_interrupt_event = interrupt_event

    else:
        if independent:
            kwargs['preexec_fn'] = lambda: os.setsid()
        else:
            env['JPY_PARENT_PID'] = str(os.getpid())
        
        proc = Popen(cmd, **kwargs)

    # Clean up pipes created to work around Popen bug.
    if redirect_in:
        if stdin is None:
            proc.stdin.close()

    return proc

__all__ = [
    'swallow_argv',
    'make_ipkernel_cmd',
    'launch_kernel',
]
