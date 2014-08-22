"""Tornado handlers for kernels."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import logging
from tornado import web

from IPython.utils.jsonutil import date_default
from IPython.utils.py3compat import string_types
from IPython.html.utils import url_path_join, url_escape

from ...base.handlers import IPythonHandler, json_errors
from ...base.zmqhandlers import AuthenticatedZMQStreamHandler

from IPython.core.release import kernel_protocol_version

class MainKernelHandler(IPythonHandler):

    @web.authenticated
    @json_errors
    def get(self):
        km = self.kernel_manager
        self.finish(json.dumps(km.list_kernels()))

    @web.authenticated
    @json_errors
    def post(self):
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, "No JSON data provided")
        try:
            name = model['name']
        except KeyError:
            raise web.HTTPError(400, "Missing field in JSON data: name")

        km = self.kernel_manager
        kernel_id = km.start_kernel(kernel_name=name)
        model = km.kernel_model(kernel_id)
        location = url_path_join(self.base_url, 'api', 'kernels', kernel_id)
        self.set_header('Location', url_escape(location))
        self.set_status(201)
        self.finish(json.dumps(model))


class KernelHandler(IPythonHandler):

    SUPPORTED_METHODS = ('DELETE', 'GET')

    @web.authenticated
    @json_errors
    def get(self, kernel_id):
        km = self.kernel_manager
        km._check_kernel_id(kernel_id)
        model = km.kernel_model(kernel_id)
        self.finish(json.dumps(model))

    @web.authenticated
    @json_errors
    def delete(self, kernel_id):
        km = self.kernel_manager
        km.shutdown_kernel(kernel_id)
        self.set_status(204)
        self.finish()


class KernelActionHandler(IPythonHandler):

    @web.authenticated
    @json_errors
    def post(self, kernel_id, action):
        km = self.kernel_manager
        if action == 'interrupt':
            km.interrupt_kernel(kernel_id)
            self.set_status(204)
        if action == 'restart':
            km.restart_kernel(kernel_id)
            model = km.kernel_model(kernel_id)
            self.set_header('Location', '{0}api/kernels/{1}'.format(self.base_url, kernel_id))
            self.write(json.dumps(model))
        self.finish()


class ZMQChannelHandler(AuthenticatedZMQStreamHandler):
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, getattr(self, 'kernel_id', 'uninitialized'))
    
    def create_stream(self):
        km = self.kernel_manager
        meth = getattr(km, 'connect_%s' % self.channel)
        self.zmq_stream = meth(self.kernel_id, identity=self.session.bsession)
        # Create a kernel_info channel to query the kernel protocol version.
        # This channel will be closed after the kernel_info reply is received.
        self.kernel_info_channel = None
        self.kernel_info_channel = km.connect_shell(self.kernel_id)
        self.kernel_info_channel.on_recv(self._handle_kernel_info_reply)
        self._request_kernel_info()
    
    def _request_kernel_info(self):
        """send a request for kernel_info"""
        self.log.debug("requesting kernel info")
        self.session.send(self.kernel_info_channel, "kernel_info_request")
    
    def _handle_kernel_info_reply(self, msg):
        """process the kernel_info_reply
        
        enabling msg spec adaptation, if necessary
        """
        idents,msg = self.session.feed_identities(msg)
        try:
            msg = self.session.unserialize(msg)
        except:
            self.log.error("Bad kernel_info reply", exc_info=True)
            self._request_kernel_info()
            return
        else:
            if msg['msg_type'] != 'kernel_info_reply' or 'protocol_version' not in msg['content']:
                self.log.error("Kernel info request failed, assuming current %s", msg['content'])
            else:
                protocol_version = msg['content']['protocol_version']
                if protocol_version != kernel_protocol_version:
                    self.session.adapt_version = int(protocol_version.split('.')[0])
                    self.log.info("adapting kernel to %s" % protocol_version)
        self.kernel_info_channel.close()
        self.kernel_info_channel = None
    
    
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
        if self.zmq_stream is None:
            return
        elif self.zmq_stream.closed():
            self.log.info("%s closed, closing websocket.", self)
            self.close()
            return
        msg = json.loads(msg)
        self.session.send(self.zmq_stream, msg)

    def on_close(self):
        # This method can be called twice, once by self.kernel_died and once
        # from the WebSocket close event. If the WebSocket connection is
        # closed before the ZMQ streams are setup, they could be None.
        if self.zmq_stream is not None and not self.zmq_stream.closed():
            self.zmq_stream.on_recv(None)
            # close the socket directly, don't wait for the stream
            socket = self.zmq_stream.socket
            self.zmq_stream.close()
            socket.close()


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
        self.write_message(json.dumps(msg, default=date_default))

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
    (r"/api/kernels", MainKernelHandler),
    (r"/api/kernels/%s" % _kernel_id_regex, KernelHandler),
    (r"/api/kernels/%s/%s" % (_kernel_id_regex, _kernel_action_regex), KernelActionHandler),
    (r"/api/kernels/%s/iopub" % _kernel_id_regex, IOPubHandler),
    (r"/api/kernels/%s/shell" % _kernel_id_regex, ShellHandler),
    (r"/api/kernels/%s/stdin" % _kernel_id_regex, StdinHandler)
]
