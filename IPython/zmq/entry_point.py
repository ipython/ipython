""" Defines helper functions for creating kernel entry points and process
launchers.
"""

# Standard library imports.
import socket
from subprocess import Popen
import sys

# System library imports.
import zmq

# Local imports.
from IPython.external.argparse import ArgumentParser
from exitpoller import ExitPollerUnix, ExitPollerWindows
from displayhook import DisplayHook
from iostream import OutStream
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
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='set the kernel\'s IP address [default: local]')
    parser.add_argument('--xrep', type=int, metavar='PORT', default=0,
                        help='set the XREP channel port [default: random]')
    parser.add_argument('--pub', type=int, metavar='PORT', default=0,
                        help='set the PUB channel port [default: random]')
    parser.add_argument('--req', type=int, metavar='PORT', default=0,
                        help='set the REQ channel port [default: random]')

    if sys.platform == 'win32':
        parser.add_argument('--parent', type=int, metavar='HANDLE', 
                            default=0, help='kill this process if the process '
                            'with HANDLE dies')
    else:
        parser.add_argument('--parent', action='store_true', 
                            help='kill this process if its parent dies')

    return parser


def make_kernel(namespace, kernel_factory, out_stream_factory=OutStream, 
                display_hook_factory=DisplayHook):
    """ Creates a kernel.
    """
    # Create a context, a session, and the kernel sockets.
    print >>sys.__stdout__, "Starting the kernel..."
    context = zmq.Context()
    session = Session(username=u'kernel')

    reply_socket = context.socket(zmq.XREP)
    xrep_port = bind_port(reply_socket, namespace.ip, namespace.xrep)
    print >>sys.__stdout__, "XREP Channel on port", xrep_port

    pub_socket = context.socket(zmq.PUB)
    pub_port = bind_port(pub_socket, namespace.ip, namespace.pub)
    print >>sys.__stdout__, "PUB Channel on port", pub_port

    req_socket = context.socket(zmq.XREQ)
    req_port = bind_port(req_socket, namespace.ip, namespace.req)
    print >>sys.__stdout__, "REQ Channel on port", req_port

    # Redirect input streams and set a display hook.
    sys.stdout = out_stream_factory(session, pub_socket, u'stdout')
    sys.stderr = out_stream_factory(session, pub_socket, u'stderr')
    sys.displayhook = display_hook_factory(session, pub_socket)

    # Create the kernel.
    return kernel_factory(session=session, reply_socket=reply_socket, 
                          pub_socket=pub_socket, req_socket=req_socket)


def start_kernel(namespace, kernel):
    """ Starts a kernel.
    """
    # Configure this kernel/process to die on parent termination, if necessary.
    if namespace.parent:
        if sys.platform == 'win32':
            poller = ExitPollerWindows(namespace.parent)
        else:
            poller = ExitPollerUnix()
        poller.start()

    # Start the kernel mainloop.
    kernel.start()


def make_default_main(kernel_factory):
    """ Creates the simplest possible kernel entry point.
    """
    def main():
        namespace = make_argument_parser().parse_args()
        kernel = make_kernel(namespace, kernel_factory)
        start_kernel(namespace, kernel)
    return main


def base_launch_kernel(code, xrep_port=0, pub_port=0, req_port=0, 
                       independent=False, extra_arguments=[]):
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
    ports_needed = int(xrep_port <= 0) + int(pub_port <= 0) + int(req_port <= 0)
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

    # Build the kernel launch command.
    arguments = [ sys.executable, '-c', code, '--xrep', str(xrep_port), 
                  '--pub', str(pub_port), '--req', str(req_port) ]
    arguments.extend(extra_arguments)

    # Spawn a kernel.
    if independent:
        if sys.platform == 'win32':
            proc = Popen(['start', '/b'] + arguments, shell=True)
        else:
            proc = Popen(arguments, preexec_fn=lambda: os.setsid())
    else:
        if sys.platform == 'win32':
            from _subprocess import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS
            pid = GetCurrentProcess()
            handle = DuplicateHandle(pid, pid, pid, 0, 
                                     True, # Inheritable by new  processes.
                                     DUPLICATE_SAME_ACCESS)
            proc = Popen(arguments + ['--parent', str(int(handle))])
        else:
            proc = Popen(arguments + ['--parent'])

    return proc, xrep_port, pub_port, req_port
