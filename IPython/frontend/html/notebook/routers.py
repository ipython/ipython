import uuid
from Queue import Queue


class ZMQStreamRouter(object):

    def __init__(self, zmq_stream):
        self.zmq_stream = zmq_stream
        self._clients = {}
        self.zmq_stream.on_recv(self._on_zmq_reply)

    def register_client(self, client):
        client_id = uuid.uuid4()
        self._clients[client_id] = client
        return client_id

    def unregister_client(self, client_id):
        del self._clients[client_id]

    def copy_clients(self, router):
        # Copy the clients of another router.
        for client_id, client in router._clients.items():
            client.router = self
            self._clients[client_id] = client


class IOPubStreamRouter(ZMQStreamRouter):

    def _on_zmq_reply(self, msg_list):
        for client_id, client in self._clients.items():
            for msg in msg_list:
                client.write_message(msg)

    def forward_unicode(self, client_id, msg):
        # This is a SUB stream that we should never write to.
        pass


class ShellStreamRouter(ZMQStreamRouter):

    def __init__(self, zmq_stream):
        ZMQStreamRouter.__init__(self, zmq_stream)
        self._request_queue = Queue()

    def _on_zmq_reply(self, msg_list):
        client_id = self._request_queue.get(block=False)
        client = self._clients.get(client_id)
        if client is not None:
            for msg in msg_list:
                client.write_message(msg)

    def forward_unicode(self, client_id, msg):
        self._request_queue.put(client_id)
        self.zmq_stream.send_unicode(msg)



