"""Tornado handlers for WebSocket <-> ZMQ sockets.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

try:
    from urllib.parse import urlparse # Py 3
except ImportError:
    from urlparse import urlparse # Py 2

try:
    from http.cookies import SimpleCookie  # Py 3
except ImportError:
    from Cookie import SimpleCookie  # Py 2
import logging
from tornado import web
from tornado import websocket

from zmq.utils import jsonapi

from IPython.kernel.zmq.session import Session
from IPython.utils.jsonutil import date_default
from IPython.utils.py3compat import PY3, cast_unicode

from .handlers import IPythonHandler

#-----------------------------------------------------------------------------
# ZMQ handlers
#-----------------------------------------------------------------------------

class ZMQStreamHandler(websocket.WebSocketHandler):

    def same_origin(self):
        """Check to see that origin and host match in the headers."""

        # The difference between version 8 and 13 is that in 8 the
        # client sends a "Sec-Websocket-Origin" header and in 13 it's
        # simply "Origin".
        if self.request.headers.get("Sec-WebSocket-Version") in ("7", "8"):
            origin_header = self.request.headers.get("Sec-Websocket-Origin")
        else:
            origin_header = self.request.headers.get("Origin")

        host = self.request.headers.get("Host")

        # If no header is provided, assume we can't verify origin
        if(origin_header is None or host is None):
            return False

        parsed_origin = urlparse(origin_header)
        origin = parsed_origin.netloc

        # Check to see that origin matches host directly, including ports
        return origin == host

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
        return jsonapi.dumps(msg, default=date_default)

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


class AuthenticatedZMQStreamHandler(ZMQStreamHandler, IPythonHandler):

    def open(self, kernel_id):
        # Check to see that origin matches host directly, including ports
        if not self.same_origin():
            self.log.warn("Cross Origin WebSocket Attempt.")
            raise web.HTTPError(404)

        self.kernel_id = cast_unicode(kernel_id, 'ascii')
        self.session = Session(config=self.config)
        self.save_on_message = self.on_message
        self.on_message = self.on_first_message

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
