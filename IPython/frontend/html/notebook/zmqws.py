"""A simple WebSocket to ZMQ forwarder."""

from tornado import websocket

class ZMQWebSocketBridge(websocket.WebSocketHandler):
    """A handler to forward between a WebSocket at ZMQ socket."""

    def open(self):
        self.stream

    @property
    def stream(self):
        raise NotImplementedError("stream property must be implemented in a subclass")

    def on_message(self, message):
        self.stream.send(message)

    def on_zmq_reply(self, reply_list):
        for part in reply_list:
            self.write_message(part)

    def on_close(self):
        print "WebSocket closed"
