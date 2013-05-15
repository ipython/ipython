"""Tornado handlers for the notebook.

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
# Kernel handlers
#-----------------------------------------------------------------------------


class MainKernelHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        km = self.kernel_manager
        self.finish(jsonapi.dumps(km.list_kernel_ids()))

    @web.authenticated
    def post(self):
        km = self.kernel_manager
        nbm = self.notebook_manager
        notebook_id = self.get_argument('notebook', default=None)
        kernel_id = km.start_kernel(notebook_id, cwd=nbm.notebook_dir)
        data = {'ws_url':self.ws_url,'kernel_id':kernel_id}
        self.set_header('Location', '{0}kernels/{1}'.format(self.base_kernel_url, kernel_id))
        self.finish(jsonapi.dumps(data))


class KernelHandler(IPythonHandler):

    SUPPORTED_METHODS = ('DELETE')

    @web.authenticated
    def delete(self, kernel_id):
        km = self.kernel_manager
        km.shutdown_kernel(kernel_id)
        self.set_status(204)
        self.finish()


class KernelActionHandler(IPythonHandler):

    @web.authenticated
    def post(self, kernel_id, action):
        km = self.kernel_manager
        if action == 'interrupt':
            km.interrupt_kernel(kernel_id)
            self.set_status(204)
        if action == 'restart':
            km.restart_kernel(kernel_id)
            data = {'ws_url':self.ws_url, 'kernel_id':kernel_id}
            self.set_header('Location', '{0}kernels/{1}'.format(self.base_kernel_url, kernel_id))
            self.write(jsonapi.dumps(data))
        self.finish()


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


class ZMQChannelHandler(AuthenticatedZMQStreamHandler):
    
    @property
    def max_msg_size(self):
        return self.settings.get('max_msg_size', 65535)
    
    def create_stream(self):
        km = self.kernel_manager
        meth = getattr(km, 'connect_%s' % self.channel)
        self.zmq_stream = meth(self.kernel_id, identity=self.session.bsession)
    
    def initialize(self, *args, **kwargs):
        self.zmq_stream = None
    
    def on_first_message(self, msg):
        try:
            super(ZMQChannelHandler, self).on_first_message(msg)
        except web.HTTPError:
            self.close()
            return
        try:
            self.create_stream()
        except web.HTTPError:
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            if not self.stream.closed():
                self.stream.close()
            self.close()
        else:
            self.zmq_stream.on_recv(self._on_zmq_reply)

    def on_message(self, msg):
        if len(msg) < self.max_msg_size:
            msg = jsonapi.loads(msg)
            self.session.send(self.zmq_stream, msg)

    def on_close(self):
        # This method can be called twice, once by self.kernel_died and once
        # from the WebSocket close event. If the WebSocket connection is
        # closed before the ZMQ streams are setup, they could be None.
        if self.zmq_stream is not None and not self.zmq_stream.closed():
            self.zmq_stream.on_recv(None)
            self.zmq_stream.close()


class IOPubHandler(ZMQChannelHandler):
    channel = 'iopub'
    
    def create_stream(self):
        super(IOPubHandler, self).create_stream()
        km = self.kernel_manager
        km.add_restart_callback(self.kernel_id, self.on_kernel_restarted)
        km.add_restart_callback(self.kernel_id, self.on_restart_failed, 'dead')
    
    def on_close(self):
        km = self.kernel_manager
        if self.kernel_id in km:
            km.remove_restart_callback(
                self.kernel_id, self.on_kernel_restarted,
            )
            km.remove_restart_callback(
                self.kernel_id, self.on_restart_failed, 'dead',
            )
        super(IOPubHandler, self).on_close()
    
    def _send_status_message(self, status):
        msg = self.session.msg("status",
            {'execution_state': status}
        )
        self.write_message(jsonapi.dumps(msg, default=date_default))

    def on_kernel_restarted(self):
        logging.warn("kernel %s restarted", self.kernel_id)
        self._send_status_message('restarting')

    def on_restart_failed(self):
        logging.error("kernel %s restarted failed!", self.kernel_id)
        self._send_status_message('dead')
    
    def on_message(self, msg):
        """IOPub messages make no sense"""
        pass


class ShellHandler(ZMQChannelHandler):
    channel = 'shell'


class StdinHandler(ZMQChannelHandler):
    channel = 'stdin'


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"

default_handlers = [
    (r"/kernels", MainKernelHandler),
    (r"/kernels/%s" % _kernel_id_regex, KernelHandler),
    (r"/kernels/%s/%s" % (_kernel_id_regex, _kernel_action_regex), KernelActionHandler),
    (r"/kernels/%s/iopub" % _kernel_id_regex, IOPubHandler),
    (r"/kernels/%s/shell" % _kernel_id_regex, ShellHandler),
    (r"/kernels/%s/stdin" % _kernel_id_regex, StdinHandler)
]
