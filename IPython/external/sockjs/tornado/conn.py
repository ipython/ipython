# -*- coding: utf-8 -*-
"""
    sockjs.tornado.conn
    ~~~~~~~~~~~~~~~~~~~

    SockJS connection interface
"""


class SockJSConnection(object):
    def __init__(self, session):
        """Connection constructor.

        `session`
            Associated session
        """
        self.session = session

    # Public API
    def on_open(self, request):
        """Default on_open() handler.

        Override when you need to do some initialization or request validation.
        If you return False, connection will be rejected.

        You can also throw Tornado HTTPError to close connection.

        `request`
            ``ConnectionInfo`` object which contains caller IP address, query string
            parameters and cookies associated with this request (if any).
        """
        pass

    def on_message(self, message):
        """Default on_message handler. Must be overridden in your application"""
        raise NotImplementedError()

    def on_close(self):
        """Default on_close handler."""
        pass

    def send(self, message, binary=False):
        """Send message to the client.

        `message`
            Message to send.
        """
        if not self.is_closed:
            self.session.send_message(message, binary=binary)

    def broadcast(self, clients, message):
        """Broadcast message to the one or more clients.
        Use this method if you want to send same message to lots of clients, as
        it contains several optimizations and will work fast than just having loop
        in your code.

        `clients`
            Clients iterable
        `message`
            Message to send.
        """
        self.session.broadcast(clients, message)

    def close(self):
        self.session.close()

    @property
    def is_closed(self):
        """Check if connection was closed"""
        return self.session.is_closed
