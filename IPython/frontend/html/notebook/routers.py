"""Routers that connect WebSockets to ZMQ sockets."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import uuid
from Queue import Queue
import json

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance, Int, Dict

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

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

    def _reserialize_reply(self, msg_list):
        """Reserialize a reply message using JSON.

        This takes the msg list from the ZMQ socket, unserializes it using
        self.session and then serializes the result using JSON. This method
        should be used by self._on_zmq_reply to build messages that can
        be sent back to the browser.
        """
        idents, msg_list = self.session.feed_identities(msg_list)
        msg = self.session.unserialize(msg_list)
        msg['header'].pop('date')
        return json.dumps(msg)


class IOPubStreamRouter(ZMQStreamRouter):

    def _on_zmq_reply(self, msg_list):
        msg = self._reserialize_reply(msg_list)
        for client_id, client in self._clients.items():
            client.write_message(msg)


class ShellStreamRouter(ZMQStreamRouter):

    _request_queue = Instance(Queue,(),{})

    def _on_zmq_reply(self, msg_list):
        msg = self._reserialize_reply(msg_list)
        client_id = self._request_queue.get(block=False)
        client = self._clients.get(client_id)
        if client is not None:
            client.write_message(msg)

    def forward_msg(self, client_id, msg):
        if len(msg) < self.max_msg_size:
            msg = json.loads(msg)
            to_send = self.session.serialize(msg)
            self._request_queue.put(client_id)        
            self.session.send(self.zmq_stream, msg)

