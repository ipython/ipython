"""WebsocketProtocol76 from tornado 3.2.2 for tornado >= 4.0

The contents of this file are Copyright (c) Tornado
Used under the Apache 2.0 license
"""


from __future__ import absolute_import, division, print_function, with_statement
# Author: Jacob Kristhammar, 2010

import functools
import hashlib
import struct
import time
import tornado.escape
import tornado.web

from tornado.log import gen_log, app_log
from tornado.util import bytes_type, unicode_type

from tornado.websocket import WebSocketHandler, WebSocketProtocol13

class AllowDraftWebSocketHandler(WebSocketHandler):
    """Restore Draft76 support for tornado 4
    
    Remove when we can run tests without phantomjs + qt4
    """
    
    # get is unmodified except between the BEGIN/END PATCH lines
    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        self.open_args = args
        self.open_kwargs = kwargs

        # Upgrade header should be present and should be equal to WebSocket
        if self.request.headers.get("Upgrade", "").lower() != 'websocket':
            self.set_status(400)
            self.finish("Can \"Upgrade\" only to \"WebSocket\".")
            return

        # Connection header should be upgrade. Some proxy servers/load balancers
        # might mess with it.
        headers = self.request.headers
        connection = map(lambda s: s.strip().lower(), headers.get("Connection", "").split(","))
        if 'upgrade' not in connection:
            self.set_status(400)
            self.finish("\"Connection\" must be \"Upgrade\".")
            return

        # Handle WebSocket Origin naming convention differences
        # The difference between version 8 and 13 is that in 8 the
        # client sends a "Sec-Websocket-Origin" header and in 13 it's
        # simply "Origin".
        if "Origin" in self.request.headers:
            origin = self.request.headers.get("Origin")
        else:
            origin = self.request.headers.get("Sec-Websocket-Origin", None)


        # If there was an origin header, check to make sure it matches
        # according to check_origin. When the origin is None, we assume it
        # did not come from a browser and that it can be passed on.
        if origin is not None and not self.check_origin(origin):
            self.set_status(403)
            self.finish("Cross origin websockets not allowed")
            return

        self.stream = self.request.connection.detach()
        self.stream.set_close_callback(self.on_connection_close)

        if self.request.headers.get("Sec-WebSocket-Version") in ("7", "8", "13"):
            self.ws_connection = WebSocketProtocol13(self)
            self.ws_connection.accept_connection()
        #--------------- BEGIN PATCH ----------------
        elif (self.allow_draft76() and
              "Sec-WebSocket-Version" not in self.request.headers):
            self.ws_connection = WebSocketProtocol76(self)
            self.ws_connection.accept_connection()
        #--------------- END PATCH ----------------
        else:
            if not self.stream.closed():
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 426 Upgrade Required\r\n"
                    "Sec-WebSocket-Version: 8\r\n\r\n"))
                self.stream.close()
    
    # 3.2 methods removed in 4.0:
    def allow_draft76(self):
        """Using this class allows draft76 connections by default"""
        return True
    
    def get_websocket_scheme(self):
        """Return the url scheme used for this request, either "ws" or "wss".
        This is normally decided by HTTPServer, but applications
        may wish to override this if they are using an SSL proxy
        that does not provide the X-Scheme header as understood
        by HTTPServer.
        Note that this is only used by the draft76 protocol.
        """
        return "wss" if self.request.protocol == "https" else "ws"
    


# No modifications from tornado-3.2.2 below this line

class WebSocketProtocol(object):
    """Base class for WebSocket protocol versions.
    """
    def __init__(self, handler):
        self.handler = handler
        self.request = handler.request
        self.stream = handler.stream
        self.client_terminated = False
        self.server_terminated = False

    def async_callback(self, callback, *args, **kwargs):
        """Wrap callbacks with this if they are used on asynchronous requests.

        Catches exceptions properly and closes this WebSocket if an exception
        is uncaught.
        """
        if args or kwargs:
            callback = functools.partial(callback, *args, **kwargs)

        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception:
                app_log.error("Uncaught exception in %s",
                              self.request.path, exc_info=True)
                self._abort()
        return wrapper

    def on_connection_close(self):
        self._abort()

    def _abort(self):
        """Instantly aborts the WebSocket connection by closing the socket"""
        self.client_terminated = True
        self.server_terminated = True
        self.stream.close()  # forcibly tear down the connection
        self.close()  # let the subclass cleanup


class WebSocketProtocol76(WebSocketProtocol):
    """Implementation of the WebSockets protocol, version hixie-76.

    This class provides basic functionality to process WebSockets requests as
    specified in
    http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76
    """
    def __init__(self, handler):
        WebSocketProtocol.__init__(self, handler)
        self.challenge = None
        self._waiting = None

    def accept_connection(self):
        try:
            self._handle_websocket_headers()
        except ValueError:
            gen_log.debug("Malformed WebSocket request received")
            self._abort()
            return

        scheme = self.handler.get_websocket_scheme()

        # draft76 only allows a single subprotocol
        subprotocol_header = ''
        subprotocol = self.request.headers.get("Sec-WebSocket-Protocol", None)
        if subprotocol:
            selected = self.handler.select_subprotocol([subprotocol])
            if selected:
                assert selected == subprotocol
                subprotocol_header = "Sec-WebSocket-Protocol: %s\r\n" % selected

        # Write the initial headers before attempting to read the challenge.
        # This is necessary when using proxies (such as HAProxy), which
        # need to see the Upgrade headers before passing through the
        # non-HTTP traffic that follows.
        self.stream.write(tornado.escape.utf8(
            "HTTP/1.1 101 WebSocket Protocol Handshake\r\n"
            "Upgrade: WebSocket\r\n"
            "Connection: Upgrade\r\n"
            "Server: TornadoServer/%(version)s\r\n"
            "Sec-WebSocket-Origin: %(origin)s\r\n"
            "Sec-WebSocket-Location: %(scheme)s://%(host)s%(uri)s\r\n"
            "%(subprotocol)s"
            "\r\n" % (dict(
                version=tornado.version,
                origin=self.request.headers["Origin"],
                scheme=scheme,
                host=self.request.host,
                uri=self.request.uri,
                subprotocol=subprotocol_header))))
        self.stream.read_bytes(8, self._handle_challenge)

    def challenge_response(self, challenge):
        """Generates the challenge response that's needed in the handshake

        The challenge parameter should be the raw bytes as sent from the
        client.
        """
        key_1 = self.request.headers.get("Sec-Websocket-Key1")
        key_2 = self.request.headers.get("Sec-Websocket-Key2")
        try:
            part_1 = self._calculate_part(key_1)
            part_2 = self._calculate_part(key_2)
        except ValueError:
            raise ValueError("Invalid Keys/Challenge")
        return self._generate_challenge_response(part_1, part_2, challenge)

    def _handle_challenge(self, challenge):
        try:
            challenge_response = self.challenge_response(challenge)
        except ValueError:
            gen_log.debug("Malformed key data in WebSocket request")
            self._abort()
            return
        self._write_response(challenge_response)

    def _write_response(self, challenge):
        self.stream.write(challenge)
        self.async_callback(self.handler.open)(*self.handler.open_args, **self.handler.open_kwargs)
        self._receive_message()

    def _handle_websocket_headers(self):
        """Verifies all invariant- and required headers

        If a header is missing or have an incorrect value ValueError will be
        raised
        """
        fields = ("Origin", "Host", "Sec-Websocket-Key1",
                  "Sec-Websocket-Key2")
        if not all(map(lambda f: self.request.headers.get(f), fields)):
            raise ValueError("Missing/Invalid WebSocket headers")

    def _calculate_part(self, key):
        """Processes the key headers and calculates their key value.

        Raises ValueError when feed invalid key."""
        # pyflakes complains about variable reuse if both of these lines use 'c'
        number = int(''.join(c for c in key if c.isdigit()))
        spaces = len([c2 for c2 in key if c2.isspace()])
        try:
            key_number = number // spaces
        except (ValueError, ZeroDivisionError):
            raise ValueError
        return struct.pack(">I", key_number)

    def _generate_challenge_response(self, part_1, part_2, part_3):
        m = hashlib.md5()
        m.update(part_1)
        m.update(part_2)
        m.update(part_3)
        return m.digest()

    def _receive_message(self):
        self.stream.read_bytes(1, self._on_frame_type)

    def _on_frame_type(self, byte):
        frame_type = ord(byte)
        if frame_type == 0x00:
            self.stream.read_until(b"\xff", self._on_end_delimiter)
        elif frame_type == 0xff:
            self.stream.read_bytes(1, self._on_length_indicator)
        else:
            self._abort()

    def _on_end_delimiter(self, frame):
        if not self.client_terminated:
            self.async_callback(self.handler.on_message)(
                frame[:-1].decode("utf-8", "replace"))
        if not self.client_terminated:
            self._receive_message()

    def _on_length_indicator(self, byte):
        if ord(byte) != 0x00:
            self._abort()
            return
        self.client_terminated = True
        self.close()

    def write_message(self, message, binary=False):
        """Sends the given message to the client of this Web Socket."""
        if binary:
            raise ValueError(
                "Binary messages not supported by this version of websockets")
        if isinstance(message, unicode_type):
            message = message.encode("utf-8")
        assert isinstance(message, bytes_type)
        self.stream.write(b"\x00" + message + b"\xff")

    def write_ping(self, data):
        """Send ping frame."""
        raise ValueError("Ping messages not supported by this version of websockets")

    def close(self):
        """Closes the WebSocket connection."""
        if not self.server_terminated:
            if not self.stream.closed():
                self.stream.write("\xff\x00")
            self.server_terminated = True
        if self.client_terminated:
            if self._waiting is not None:
                self.stream.io_loop.remove_timeout(self._waiting)
            self._waiting = None
            self.stream.close()
        elif self._waiting is None:
            self._waiting = self.stream.io_loop.add_timeout(
                time.time() + 5, self._abort)

