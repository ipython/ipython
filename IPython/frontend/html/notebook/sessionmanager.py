"""A manager for session and channels for a single kernel."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import zmq
from zmq.eventloop.zmqstream import ZMQStream

from IPython.utils.traitlets import Instance, Dict, CBytes, Bool
from IPython.zmq.session import SessionFactory


class SessionManagerRunningError(Exception):
    pass

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class SessionManager(SessionFactory):
    """Manages a session for a kernel.

    The object manages a variety of things for a connection session to
    a running kernel:

    * The set of channels or connected ZMQ streams to the kernel.
    * An IPython.zmq.session.Session object that manages send/recv logic
      for those channels.
    """

    kernel_manager = Instance('IPython.frontend.html.notebook.kernelmanager.KernelManager')
    kernel_id = CBytes(b'')
    _session_streams = Dict()
    _running = Bool(False)

    def __init__(self, **kwargs):
        kernel_id = kwargs.pop('kernel_id')
        super(SessionManager, self).__init__(**kwargs)
        self.kernel_id = kernel_id
        self.start()

    def __del__(self):
        self.stop()

    def start(self):
        if not self._running:
            ports = self.kernel_manager.get_kernel_ports(self.kernel_id)
            iopub_stream = self.create_connected_stream(ports['iopub_port'], zmq.SUB)
            iopub_stream.socket.setsockopt(zmq.SUBSCRIBE, b'')
            shell_stream = self.create_connected_stream(ports['shell_port'], zmq.XREQ)
            self._session_streams = dict(
                iopub_stream = iopub_stream,
                shell_stream = shell_stream
            )
            self._running = True
        else:
            raise SessionManagerRunningError(
                'Session manager is already running, call stop() before start()'
            )

    def stop(self):
        if self._running:
            for name, stream in self._session_streams.items():
                stream.close()
            self._session_streams = {}
            self._running = False

    def create_connected_stream(self, port, socket_type):
        sock = self.context.socket(socket_type)
        addr = "tcp://%s:%i" % (self.kernel_manager.get_kernel_ip(self.kernel_id), port)
        self.log.info("Connecting to: %s" % addr)
        sock.connect(addr)
        return ZMQStream(sock)

    def get_iopub_stream(self):
        return self._session_streams['iopub_stream']

    def get_shell_stream(self):
        return self._session_streams['shell_stream']


