import uuid
from Queue import Queue
import json

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance, Int, Dict

class ZMQStreamRouter(Configurable):

    zmq_stream = Instance('zmq.eventloop.zmqstream.ZMQStream')
    session = Instance('IPython.zmq.session.Session')
    max_msg_size = Int(2048, config=True, help="""
        The max raw message size accepted from the browser
        over a WebSocket connection.
    """)

    _clients = Dict()

    def __init__(self, **kwargs):
        super(ZMQStreamRouter,self).__init__(**kwargs)
        self.zmq_stream.on_recv(self._on_zmq_reply)

    def register_client(self, client):
        """Register a client, returning a client uuid."""
        client_id = uuid.uuid4()
        self._clients[client_id] = client
        return client_id

    def unregister_client(self, client_id):
        """Unregister a client by its client uuid."""
        del self._clients[client_id]

    def copy_clients(self, router):
        """Copy the clients of another router to this one.

        This is used to enable the backend zeromq stream to disconnect
        and reconnect while the WebSocket connections to browsers
        remain, such as when a kernel is restarted.
        """
        for client_id, client in router._clients.items():
            client.router = self
            self._clients[client_id] = client

    def forward_msg(self, client_id, msg):
        """Forward a msg to a client by its id.

        The default implementation of this will fail silently if a message
        arrives on a socket that doesn't support it. This method should
        use max_msg_size to check and silently discard message that are too
        long."""
        pass

    def _on_zmq_reply(self, msg_list):
        """Handle a message the ZMQ stream sends to the router.

        Usually, this is where the return message will be written to
        clients that need it using client.write_message().
        """
        pass


class IOPubStreamRouter(ZMQStreamRouter):

    def _on_zmq_reply(self, msg_list):
        msg = self.session.unpack_message(msg_list)
        msg = json.dumps(msg)
        for client_id, client in self._clients.items():
            for msg in msg_list:
                client.write_message(msg)


class ShellStreamRouter(ZMQStreamRouter):

    _request_queue = Instance(Queue,(),{})

    def _on_zmq_reply(self, msg_list):
        msg = self.session.unpack_message(msg_list)
        msg = json.dumps(msg)
        print "Reply: ", msg_list
        client_id = self._request_queue.get(block=False)
        client = self._clients.get(client_id)
        if client is not None:
            for msg in msg_list:
                client.write_message(msg)

    def forward_msg(self, client_id, msg):
        if len(msg) < self.max_msg_size:
            msg = json.loads(msg)
            print "Raw msg: ", msg
            to_send = self.session.serialize(msg)
            print "to_send: ", to_send, to_send[-3:]
            self._request_queue.put(client_id)        
            self.session.send_raw(self.zmq_stream, to_send[-3:])

