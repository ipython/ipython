""" Defines helper functions for creating kernel entry points and process
launchers.
"""

# Standard library imports.
import atexit
import os
import socket
from subprocess import Popen, PIPE
import sys

# Local imports.
from parentpoller import ParentPollerWindows



def base_launch_kernel(code, shell_port=0, iopub_port=0, stdin_port=0, hb_port=0,
                        ip=None, stdin=None, stdout=None, stderr=None,
                        executable=None, independent=False, extra_arguments=[]):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    code : str,
        A string of Python code that imports and executes a kernel entry point.

    shell_port : int, optional
        The port to use for XREP channel.

    iopub_port : int, optional
        The port to use for the SUB channel.

    stdin_port : int, optional
        The port to use for the REQ (raw input) channel.

    hb_port : int, optional
        The port to use for the hearbeat REP channel.

    ip  : str, optional
        The ip address the kernel will bind to.

    stdin, stdout, stderr : optional (default None)
        Standards streams, as defined in subprocess.Popen.

    executable : str, optional (default sys.executable)
        The Python executable to use for the kernel process.

    independent : bool, optional (default False) 
        If set, the kernel process is guaranteed to survive if this process
        dies. If not set, an effort is made to ensure that the kernel is killed
        when this process dies. Note that in this case it is still good practice
        to kill kernels manually before exiting.

    extra_arguments = list, optional
        A list of extra arguments to pass when executing the launch code.

    Returns
    -------
    A tuple of form:
        (kernel_process, shell_port, iopub_port, stdin_port, hb_port)
    where kernel_process is a Popen object and the ports are integers.
    """
    # Find open ports as necessary.
    ports = []
    ports_needed = int(shell_port <= 0) + int(iopub_port <= 0) + \
                   int(stdin_port <= 0) + int(hb_port <= 0)
    for i in xrange(ports_needed):
        sock = socket.socket()
        sock.bind(('', 0))
        ports.append(sock)
    for i, sock in enumerate(ports):
        port = sock.getsockname()[1]
        sock.close()
        ports[i] = port
    if shell_port <= 0:
        shell_port = ports.pop(0)
    if iopub_port <= 0:
        iopub_port = ports.pop(0)
    if stdin_port <= 0:
        stdin_port = ports.pop(0)
    if hb_port <= 0:
        hb_port = ports.pop(0)

    # Build the kernel launch command.
    if executable is None:
        executable = sys.executable
    arguments = [ executable, '-c', code, 'shell=%i'%shell_port, 
                  'iopub=%i'%iopub_port, 'stdin=%i'%stdin_port,
                  'hb=%i'%hb_port 
    ]
    if ip is not None:
        arguments.append('ip=%s'%ip)
    arguments.extend(extra_arguments)

    # Spawn a kernel.
    if sys.platform == 'win32':
        # Create a Win32 event for interrupting the kernel.
        interrupt_event = ParentPollerWindows.create_interrupt_event()
        arguments += [ 'interrupt=%i'%interrupt_event ]

        # If this process in running on pythonw, stdin, stdout, and stderr are
        # invalid. Popen will fail unless they are suitably redirected. We don't
        # read from the pipes, but they must exist.
        if sys.executable.endswith('pythonw.exe'):
            redirect = True
            _stdin = PIPE if stdin is None else stdin
            _stdout = PIPE if stdout is None else stdout
            _stderr = PIPE if stderr is None else stderr
        else:
            redirect = False
            _stdin, _stdout, _stderr = stdin, stdout, stderr

        # If the kernel is running on pythonw and stdout/stderr are not been
        # re-directed, it will crash when more than 4KB of data is written to
        # stdout or stderr. This is a bug that has been with Python for a very
        # long time; see http://bugs.python.org/issue706263.
        # A cleaner solution to this problem would be to pass os.devnull to
        # Popen directly. Unfortunately, that does not work.
        if executable.endswith('pythonw.exe'):
            if stdout is None:
                arguments.append('--no-stdout')
            if stderr is None:
                arguments.append('--no-stderr')

        # Launch the kernel process.
        if independent:
            proc = Popen(arguments, 
                         creationflags=512, # CREATE_NEW_PROCESS_GROUP
                         stdin=_stdin, stdout=_stdout, stderr=_stderr)
        else:
            from _subprocess import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS
            pid = GetCurrentProcess()
            handle = DuplicateHandle(pid, pid, pid, 0, 
                                     True, # Inheritable by new processes.
                                     DUPLICATE_SAME_ACCESS)
            proc = Popen(arguments + ['parent=%i'%int(handle)],
                         stdin=_stdin, stdout=_stdout, stderr=_stderr)

        # Attach the interrupt event to the Popen objet so it can be used later.
        proc.win32_interrupt_event = interrupt_event

        # Clean up pipes created to work around Popen bug.
        if redirect:
            if stdin is None:
                proc.stdin.close()
            if stdout is None:
                proc.stdout.close()
            if stderr is None:
                proc.stderr.close()

    else:
        if independent:
            proc = Popen(arguments, preexec_fn=lambda: os.setsid(),
                         stdin=stdin, stdout=stdout, stderr=stderr)
        else:
            proc = Popen(arguments + ['parent=1'],
                         stdin=stdin, stdout=stdout, stderr=stderr)

    return proc, shell_port, iopub_port, stdin_port, hb_port
