"""Tornado handlers for WebSocket <-> ZMQ sockets."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json

try:
    from urllib.parse import urlparse # Py 3
except ImportError:
    from urlparse import urlparse # Py 2

try:
    from http.cookies import SimpleCookie  # Py 3
except ImportError:
    from Cookie import SimpleCookie  # Py 2
import logging

import tornado
from tornado import ioloop
from tornado import web
from tornado import websocket

from IPython.kernel.zmq.session import Session
from IPython.utils.jsonutil import date_default
from IPython.utils.py3compat import PY3, cast_unicode

from .handlers import IPythonHandler


class ZMQStreamHandler(websocket.WebSocketHandler):
    
    def check_origin(self, origin):
        """Check Origin == Host or Access-Control-Allow-Origin.
        
        Tornado >= 4 calls this method automatically, raising 403 if it returns False.
        We call it explicitly in `open` on Tornado < 4.
        """
        if self.allow_origin == '*':
            return True

        host = self.request.headers.get("Host")

        # If no header is provided, assume we can't verify origin
        if origin is None:
            self.log.warn("Missing Origin header, rejecting WebSocket connection.")
            return False
        if host is None:
            self.log.warn("Missing Host header, rejecting WebSocket connection.")
            return False
        
        origin = origin.lower()
        origin_host = urlparse(origin).netloc
        
        # OK if origin matches host
        if origin_host == host:
            return True
        
        # Check CORS headers
        if self.allow_origin:
            allow = self.allow_origin == origin
        elif self.allow_origin_pat:
            allow = bool(self.allow_origin_pat.match(origin))
        else:
            # No CORS headers deny the request
            allow = False
        if not allow:
            self.log.warn("Blocking Cross Origin WebSocket Attempt.  Origin: %s, Host: %s",
                origin, host,
            )
        return allow

    def clear_cookie(self, *args, **kwargs):
        """meaningless for websockets"""
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
        try:
            msg['header'].pop('date')
        except KeyError:
            pass
        try:
            msg['parent_header'].pop('date')
        except KeyError:
            pass
        msg.pop('buffers')
        return json.dumps(msg, default=date_default)

    def _on_zmq_reply(self, msg_list):
        # Sometimes this gets triggered when the on_close method is scheduled in the
        # eventloop but hasn't been called.
        if self.stream.closed(): return
        try:
            msg = self._reserialize_reply(msg_list)
        except Exception:
            self.log.critical("Malformed message: %r" % msg_list, exc_info=True)
        else:
            self.write_message(msg)

    def allow_draft76(self):
        """Allow draft 76, until browsers such as Safari update to RFC 6455.
        
        This has been disabled by default in tornado in release 2.2.0, and
        support will be removed in later versions.
        """
        return True

# ping interval for keeping websockets alive (30 seconds)
WS_PING_INTERVAL = 30000

class AuthenticatedZMQStreamHandler(ZMQStreamHandler, IPythonHandler):
    ping_callback = None
    last_ping = 0
    last_pong = 0
    
    @property
    def ping_interval(self):
        """The interval for websocket keep-alive pings.
        
        Set ws_ping_interval = 0 to disable pings.
        """
        return self.settings.get('ws_ping_interval', WS_PING_INTERVAL)
    
    @property
    def ping_timeout(self):
        """If no ping is received in this many milliseconds,
        close the websocket connection (VPNs, etc. can fail to cleanly close ws connections).
        Default is max of 3 pings or 30 seconds.
        """
        return self.settings.get('ws_ping_timeout',
            max(3 * self.ping_interval, WS_PING_INTERVAL)
        )

    def set_default_headers(self):
        """Undo the set_default_headers in IPythonHandler
        
        which doesn't make sense for websockets
        """
        pass

    def open(self, kernel_id):
        self.kernel_id = cast_unicode(kernel_id, 'ascii')
        # Check to see that origin matches host directly, including ports
        # Tornado 4 already does CORS checking
        if tornado.version_info[0] < 4:
            if not self.check_origin(self.get_origin()):
                raise web.HTTPError(403)

        self.session = Session(config=self.config)
        self.save_on_message = self.on_message
        self.on_message = self.on_first_message
        
        # start the pinging
        if self.ping_interval > 0:
            self.last_ping = ioloop.IOLoop.instance().time()  # Remember time of last ping
            self.last_pong = self.last_ping
            self.ping_callback = ioloop.PeriodicCallback(self.send_ping, self.ping_interval)
            self.ping_callback.start()

    def send_ping(self):
        """send a ping to keep the websocket alive"""
        if self.stream.closed() and self.ping_callback is not None:
            self.ping_callback.stop()
            return
        
        # check for timeout on pong.  Make sure that we really have sent a recent ping in
        # case the machine with both server and client has been suspended since the last ping.
        now = ioloop.IOLoop.instance().time()
        since_last_pong = 1e3 * (now - self.last_pong)
        since_last_ping = 1e3 * (now - self.last_ping)
        if since_last_ping < 2*self.ping_interval and since_last_pong > self.ping_timeout:
            self.log.warn("WebSocket ping timeout after %i ms.", since_last_pong)
            self.close()
            return

        self.ping(b'')
        self.last_ping = now

    def on_pong(self, data):
        self.last_pong = ioloop.IOLoop.instance().time()

    def _inject_cookie_message(self, msg):
        """Inject the first message, which is the document cookie,
        for authentication."""
        if not PY3 and isinstance(msg, unicode):
            # Cookie constructor doesn't accept unicode strings
            # under Python 2.x for some reason
            msg = msg.encode('utf8', 'replace')
        try:
            identity, msg = msg.split(':', 1)
            self.session.session = cast_unicode(identity, 'ascii')
        except Exception:
            logging.error("First ws message didn't have the form 'identity:[cookie]' - %r", msg)
        
        try:
            self.request._cookies = SimpleCookie(msg)
        except:
            self.log.warn("couldn't parse cookie string: %s",msg, exc_info=True)

    def on_first_message(self, msg):
        self._inject_cookie_message(msg)
        if self.get_current_user() is None:
            self.log.warn("Couldn't authenticate WebSocket connection")
            raise web.HTTPError(403)
        self.on_message = self.save_on_message
