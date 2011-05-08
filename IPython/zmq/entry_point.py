""" Defines helper functions for creating kernel entry points and process
launchers.
"""

# Standard library imports.
import atexit
import os
import socket
from subprocess import Popen, PIPE
import sys

# System library imports.
import zmq

# Local imports.
from IPython.core.ultratb import FormattedTB
from IPython.external.argparse import ArgumentParser
from IPython.utils import io
from IPython.utils.localinterfaces import LOCALHOST
from displayhook import DisplayHook
from heartbeat import Heartbeat
from iostream import OutStream
from parentpoller import ParentPollerUnix, ParentPollerWindows
from session import Session

def bind_port(socket, ip, port):
    """ Binds the specified ZMQ socket. If the port is zero, a random port is
    chosen. Returns the port that was bound.
    """
    connection = 'tcp://%s' % ip
    if port <= 0:
        port = socket.bind_to_random_port(connection)
    else:
        connection += ':%i' % port
        socket.bind(connection)
    return port


def make_argument_parser():
    """ Creates an ArgumentParser for the generic arguments supported by all 
    kernel entry points.
    """
    parser = ArgumentParser()
    parser.add_argument('--ip', type=str, default=LOCALHOST,
                        help='set the kernel\'s IP address [default: local]')
    parser.add_argument('--xrep', type=int, metavar='PORT', default=0,
                        help='set the XREP channel port [default: random]')
    parser.add_argument('--pub', type=int, metavar='PORT', default=0,
                        help='set the PUB channel port [default: random]')
    parser.add_argument('--req', type=int, metavar='PORT', default=0,
                        help='set the REQ channel port [default: random]')
    parser.add_argument('--hb', type=int, metavar='PORT', default=0,
                        help='set the heartbeat port [default: random]')

    if sys.platform == 'win32':
        parser.add_argument('--interrupt', type=int, metavar='HANDLE', 
                            default=0, help='interrupt this process when '
                            'HANDLE is signaled')
        parser.add_argument('--parent', type=int, metavar='HANDLE', 
                            default=0, help='kill this process if the process '
                            'with HANDLE dies')
    else:
        parser.add_argument('--parent', action='store_true', 
                            help='kill this process if its parent dies')

    return parser


def make_kernel(namespace, kernel_factory, 
                out_stream_factory=None, display_hook_factory=None):
    """ Creates a kernel, redirects stdout/stderr, and installs a display hook
    and exception handler.
    """
    # If running under pythonw.exe, the interpreter will crash if more than 4KB
    # of data is written to stdout or stderr. This is a bug that has been with
    # Python for a very long time; see http://bugs.python.org/issue706263.
    if sys.executable.endswith('pythonw.exe'):
        blackhole = file(os.devnull, 'w')
        sys.stdout = sys.stderr = blackhole
        sys.__stdout__ = sys.__stderr__ = blackhole 

    # Install minimal exception handling
    sys.excepthook = FormattedTB(mode='Verbose', color_scheme='NoColor', 
                                 ostream=sys.__stdout__)

    # Create a context, a session, and the kernel sockets.
    io.raw_print("Starting the kernel at pid:", os.getpid())
    context = zmq.Context()
    # Uncomment this to try closing the context.
    # atexit.register(context.close)
    session = Session(username=u'kernel')

    reply_socket = context.socket(zmq.XREP)
    xrep_port = bind_port(reply_socket, namespace.ip, namespace.xrep)
    io.raw_print("XREP Channel on port", xrep_port)

    pub_socket = context.socket(zmq.PUB)
    pub_port = bind_port(pub_socket, namespace.ip, namespace.pub)
    io.raw_print("PUB Channel on port", pub_port)

    req_socket = context.socket(zmq.XREQ)
    req_port = bind_port(req_socket, namespace.ip, namespace.req)
    io.raw_print("REQ Channel on port", req_port)

    hb = Heartbeat(context, (namespace.ip, namespace.hb))
    hb.start()
    hb_port = hb.port
    io.raw_print("Heartbeat REP Channel on port", hb_port)

    # Helper to make it easier to connect to an existing kernel, until we have
    # single-port connection negotiation fully implemented.
    io.raw_print("To connect another client to this kernel, use:")
    io.raw_print("-e --xreq {0} --sub {1} --rep {2} --hb {3}".format(
        xrep_port, pub_port, req_port, hb_port))

    # Redirect input streams and set a display hook.
    if out_stream_factory:
        sys.stdout = out_stream_factory(session, pub_socket, u'stdout')
        sys.stderr = out_stream_factory(session, pub_socket, u'stderr')
    if display_hook_factory:
        sys.displayhook = display_hook_factory(session, pub_socket)

    # Create the kernel.
    kernel = kernel_factory(session=session, reply_socket=reply_socket, 
                            pub_socket=pub_socket, req_socket=req_socket)
    kernel.record_ports(xrep_port=xrep_port, pub_port=pub_port,
                        req_port=req_port, hb_port=hb_port)
    return kernel


def start_kernel(namespace, kernel):
    """ Starts a kernel.
    """
    # Configure this kernel process to poll the parent process, if necessary.
    if sys.platform == 'win32':
        if namespace.interrupt or namespace.parent:
            poller = ParentPollerWindows(namespace.interrupt, namespace.parent)
            poller.start()
    elif namespace.parent:
        poller = ParentPollerUnix()
        poller.start()

    # Start the kernel mainloop.
    kernel.start()


def make_default_main(kernel_factory):
    """ Creates the simplest possible kernel entry point.
    """
    def main():
        namespace = make_argument_parser().parse_args()
        kernel = make_kernel(namespace, kernel_factory, OutStream, DisplayHook)
        start_kernel(namespace, kernel)
    return main


def base_launch_kernel(code, xrep_port=0, pub_port=0, req_port=0, hb_port=0,
                       executable=None, independent=False, extra_arguments=[]):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    code : str,
        A string of Python code that imports and executes a kernel entry point.

    xrep_port : int, optional
        The port to use for XREP channel.

    pub_port : int, optional
        The port to use for the SUB channel.

    req_port : int, optional
        The port to use for the REQ (raw input) channel.

    hb_port : int, optional
        The port to use for the hearbeat REP channel.

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
        (kernel_process, xrep_port, pub_port, req_port)
    where kernel_process is a Popen object and the ports are integers.
    """
    # Find open ports as necessary.
    ports = []
    ports_needed = int(xrep_port <= 0) + int(pub_port <= 0) + \
                   int(req_port <= 0) + int(hb_port <= 0)
    for i in xrange(ports_needed):
        sock = socket.socket()
        sock.bind(('', 0))
        ports.append(sock)
    for i, sock in enumerate(ports):
        port = sock.getsockname()[1]
        sock.close()
        ports[i] = port
    if xrep_port <= 0:
        xrep_port = ports.pop(0)
    if pub_port <= 0:
        pub_port = ports.pop(0)
    if req_port <= 0:
        req_port = ports.pop(0)
    if hb_port <= 0:
        hb_port = ports.pop(0)

    # Build the kernel launch command.
    if executable is None:
        executable = sys.executable
    arguments = [ executable, '-c', code, '--xrep', str(xrep_port), 
                  '--pub', str(pub_port), '--req', str(req_port),
                  '--hb', str(hb_port) ]
    arguments.extend(extra_arguments)

    # Spawn a kernel.
    if sys.platform == 'win32':
        # Create a Win32 event for interrupting the kernel.
        interrupt_event = ParentPollerWindows.create_interrupt_event()
        arguments += [ '--interrupt', str(int(interrupt_event)) ]

        # If using pythonw, stdin, stdout, and stderr are invalid. Popen will
        # fail unless they are suitably redirected. We don't read from the
        # pipes, but they must exist.
        redirect = PIPE if executable.endswith('pythonw.exe') else None

        if independent:
            proc = Popen(arguments, 
                         creationflags=512, # CREATE_NEW_PROCESS_GROUP
                         stdout=redirect, stderr=redirect, stdin=redirect)
        else:
            from _subprocess import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS
            pid = GetCurrentProcess()
            handle = DuplicateHandle(pid, pid, pid, 0, 
                                     True, # Inheritable by new processes.
                                     DUPLICATE_SAME_ACCESS)
            proc = Popen(arguments + ['--parent', str(int(handle))],
                         stdout=redirect, stderr=redirect, stdin=redirect)

        # Attach the interrupt event to the Popen objet so it can be used later.
        proc.win32_interrupt_event = interrupt_event

        # Clean up pipes created to work around Popen bug.
        if redirect is not None:
            proc.stdout.close()
            proc.stderr.close()
            proc.stdin.close()

    else:
        if independent:
            proc = Popen(arguments, preexec_fn=lambda: os.setsid())
        else:
            proc = Popen(arguments + ['--parent'])

    return proc, xrep_port, pub_port, req_port, hb_port
