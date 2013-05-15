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

import Cookie
import logging
from tornado import web
from tornado import websocket

from zmq.utils import jsonapi

from IPython.kernel.zmq.session import Session
from IPython.utils.jsonutil import date_default
from IPython.utils.py3compat import PY3

from ..base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# ZMQ handlers
#-----------------------------------------------------------------------------

class ZMQStreamHandler(websocket.WebSocketHandler):
    
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
        self.kernel_id = kernel_id.decode('ascii')
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
            self.session.session = identity.decode('ascii')
        except Exception:
            logging.error("First ws message didn't have the form 'identity:[cookie]' - %r", msg)
        
        try:
            self.request._cookies = Cookie.SimpleCookie(msg)
        except:
            self.log.warn("couldn't parse cookie string: %s",msg, exc_info=True)

    def on_first_message(self, msg):
        self._inject_cookie_message(msg)
        if self.get_current_user() is None:
            self.log.warn("Couldn't authenticate WebSocket connection")
            raise web.HTTPError(403)
        self.on_message = self.save_on_message