import logging
import uuid

import zmq
from zmq.eventloop.zmqstream import ZMQStream


class SessionManager(object):

    def __init__(self, kernel_manager, kernel_id, context):
        self.context = context
        self.kernel_manager = kernel_manager
        self.kernel_id = kernel_id
        self._sessions = {}

    def __del__(self):
        self.stop_all()

    @property
    def session_ids(self):
        return self._session.keys()

    def __len__(self):
        return len(self.session_ids)

    def __contains__(self, session_id):
        if session_id in self.session_ids:
            return True
        else:
            return False

    def start_session(self):
        session_id = str(uuid.uuid4())
        ports = self.kernel_manager.get_kernel_ports(self.kernel_id)
        iopub_stream = self.create_connected_stream(ports['iopub_port'], zmq.SUB)
        shell_stream = self.create_connected_stream(ports['shell_port'], zmq.XREQ)
        self._sessions[session_id] = dict(
            iopub_stream = iopub_stream,
            shell_stream = shell_stream
        )
        return session_id

    def stop_session(self, session_id):
        session_dict = self._sessions.get(session_id)
        if session_dict is not None:
            for name, stream in session_dict.items():
                stream.close()
            del self._sessions[session_id]

    def stop_all(self):
        for session_id in self._sessions.keys():
            self.stop_session(session_id)

    def create_connected_stream(self, port, socket_type):
        sock = self.context.socket(socket_type)
        addr = "tcp://%s:%i" % (self.kernel_manager.ip, port)
        logging.info("Connecting to: %s" % addr)
        sock.connect(addr)
        return ZMQStream(sock)

    def get_stream(self, session_id, stream_name):
        session_dict = self._sessions.get(session_id)
        if session_dict is not None:
            return session_dict[stream_name]
        else:
            raise KeyError("Session with id not found: %s" % session_id)

    def get_iopub_stream(self, session_id):
        return self.get_stream(session_id, 'iopub_stream')

    def get_shell_stream(self, session_id):
        return self.get_stream(session_id, 'shell_stream')
