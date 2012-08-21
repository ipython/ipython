# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.websocket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket transport implementation
"""
import logging
import socket

from sockjs.tornado import proto, websocket
from sockjs.tornado.transports import base


class WebSocketTransport(websocket.WebSocketHandler, base.BaseTransportMixin):
    """Websocket transport"""
    name = 'websocket'

    def initialize(self, server):
        self.server = server
        self.session = None

    def open(self, session_id):
        # Stats
        self.server.stats.on_conn_opened()

        # Disable nagle
        if self.server.settings['disable_nagle']:
            self.stream.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        # Handle session
        self.session = self.server.create_session(session_id, register=False)

        if not self.session.set_handler(self):
            self.close()
            return

        self.session.verify_state()

        if self.session:
            self.session.flush()

    def _detach(self):
        if self.session is not None:
            self.session.remove_handler(self)
            self.session = None

    def on_message(self, message):
        # Ignore empty messages
        if not message or not self.session:
            return

        try:
            msg = proto.json_decode(message)

            if isinstance(msg, list):
                self.session.on_messages(msg)
            else:
                self.session.on_messages((msg,))
        except Exception:
            logging.exception('WebSocket')

            # Close session on exception
            #self.session.close()

            # Close running connection
            self.abort_connection()

    def on_close(self):
        # Close session if websocket connection was closed
        if self.session is not None:
            # Stats
            self.server.stats.on_conn_closed()

            # Detach before closing session
            session = self.session
            self._detach()
            session.close()

    def send_pack(self, message):
        # Send message
        try:
            self.write_message(message)
        except IOError:
            self.server.io_loop.add_callback(self.on_close)

    def session_closed(self):
        # If session was closed by the application, terminate websocket
        # connection as well.
        try:
            self.close()
        except IOError:
            pass
        finally:
            self._detach()

    # Websocket overrides
    def allow_draft76(self):
        return True

    def auto_decode(self):
        return False
