"""Tornado handlers for kernels."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import logging
from tornado import gen, web
from tornado.concurrent import Future
from tornado.ioloop import IOLoop

from IPython.utils.jsonutil import date_default
from IPython.utils.py3compat import cast_unicode
from IPython.html.utils import url_path_join, url_escape

from ...base.handlers import IPythonHandler, json_errors
from ...base.zmqhandlers import AuthenticatedZMQStreamHandler, deserialize_binary_message

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
        km = self.kernel_manager
        model = self.get_json_body()
        if model is None:
            model = {
                'name': km.default_kernel_name
            }
        else:
            model.setdefault('name', km.default_kernel_name)

        kernel_id = km.start_kernel(kernel_name=model['name'])
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


class ZMQChannelsHandler(AuthenticatedZMQStreamHandler):
    
    @property
    def kernel_info_timeout(self):
        return self.settings.get('kernel_info_timeout', 10)
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, getattr(self, 'kernel_id', 'uninitialized'))
    
    def create_stream(self):
        km = self.kernel_manager
        identity = self.session.bsession
        for channel in ('shell', 'iopub', 'stdin'):
            meth = getattr(km, 'connect_' + channel)
            self.channels[channel] = stream = meth(self.kernel_id, identity=identity)
            stream.channel = channel
        km.add_restart_callback(self.kernel_id, self.on_kernel_restarted)
        km.add_restart_callback(self.kernel_id, self.on_restart_failed, 'dead')
    
    def request_kernel_info(self):
        """send a request for kernel_info"""
        km = self.kernel_manager
        kernel = km.get_kernel(self.kernel_id)
        try:
            # check for previous request
            future = kernel._kernel_info_future
        except AttributeError:
            self.log.debug("Requesting kernel info from %s", self.kernel_id)
            # Create a kernel_info channel to query the kernel protocol version.
            # This channel will be closed after the kernel_info reply is received.
            if self.kernel_info_channel is None:
                self.kernel_info_channel = km.connect_shell(self.kernel_id)
            self.kernel_info_channel.on_recv(self._handle_kernel_info_reply)
            self.session.send(self.kernel_info_channel, "kernel_info_request")
            # store the future on the kernel, so only one request is sent
            kernel._kernel_info_future = self._kernel_info_future
        else:
            if not future.done():
                self.log.debug("Waiting for pending kernel_info request")
            future.add_done_callback(lambda f: self._finish_kernel_info(f.result()))
        return self._kernel_info_future
    
    def _handle_kernel_info_reply(self, msg):
        """process the kernel_info_reply
        
        enabling msg spec adaptation, if necessary
        """
        idents,msg = self.session.feed_identities(msg)
        try:
            msg = self.session.deserialize(msg)
        except:
            self.log.error("Bad kernel_info reply", exc_info=True)
            self._kernel_info_future.set_result({})
            return
        else:
            info = msg['content']
            self.log.debug("Received kernel info: %s", info)
            if msg['msg_type'] != 'kernel_info_reply' or 'protocol_version' not in info:
                self.log.error("Kernel info request failed, assuming current %s", info)
                info = {}
            self._finish_kernel_info(info)
        
        # close the kernel_info channel, we don't need it anymore
        if self.kernel_info_channel:
            self.kernel_info_channel.close()
        self.kernel_info_channel = None
    
    def _finish_kernel_info(self, info):
        """Finish handling kernel_info reply
        
        Set up protocol adaptation, if needed,
        and signal that connection can continue.
        """
        protocol_version = info.get('protocol_version', kernel_protocol_version)
        if protocol_version != kernel_protocol_version:
            self.session.adapt_version = int(protocol_version.split('.')[0])
            self.log.info("Adapting to protocol v%s for kernel %s", protocol_version, self.kernel_id)
        if not self._kernel_info_future.done():
            self._kernel_info_future.set_result(info)
    
    def initialize(self):
        super(ZMQChannelsHandler, self).initialize()
        self.zmq_stream = None
        self.channels = {}
        self.kernel_id = None
        self.kernel_info_channel = None
        self._kernel_info_future = Future()
    
    @gen.coroutine
    def pre_get(self):
        # authenticate first
        super(ZMQChannelsHandler, self).pre_get()
        # then request kernel info, waiting up to a certain time before giving up.
        # We don't want to wait forever, because browsers don't take it well when
        # servers never respond to websocket connection requests.
        kernel = self.kernel_manager.get_kernel(self.kernel_id)
        self.session.key = kernel.session.key
        future = self.request_kernel_info()
        
        def give_up():
            """Don't wait forever for the kernel to reply"""
            if future.done():
                return
            self.log.warn("Timeout waiting for kernel_info reply from %s", self.kernel_id)
            future.set_result({})
        loop = IOLoop.current()
        loop.add_timeout(loop.time() + self.kernel_info_timeout, give_up)
        # actually wait for it
        yield future
    
    @gen.coroutine
    def get(self, kernel_id):
        self.kernel_id = cast_unicode(kernel_id, 'ascii')
        yield super(ZMQChannelsHandler, self).get(kernel_id=kernel_id)
    
    def open(self, kernel_id):
        super(ZMQChannelsHandler, self).open()
        try:
            self.create_stream()
        except web.HTTPError as e:
            self.log.error("Error opening stream: %s", e)
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            for channel, stream in self.channels.items():
                if not stream.closed():
                    stream.close()
            self.close()
        else:
            for channel, stream in self.channels.items():
                stream.on_recv_stream(self._on_zmq_reply)

    def on_message(self, msg):
        if not self.channels:
            # already closed, ignore the message
            self.log.debug("Received message on closed websocket %r", msg)
            return
        if isinstance(msg, bytes):
            msg = deserialize_binary_message(msg)
        else:
            msg = json.loads(msg)
        channel = msg.pop('channel', None)
        if channel is None:
            self.log.warn("No channel specified, assuming shell: %s", msg)
            channel = 'shell'
        if channel not in self.channels:
            self.log.warn("No such channel: %r", channel)
            return
        stream = self.channels[channel]
        self.session.send(stream, msg)

    def on_close(self):
        km = self.kernel_manager
        if self.kernel_id in km:
            km.remove_restart_callback(
                self.kernel_id, self.on_kernel_restarted,
            )
            km.remove_restart_callback(
                self.kernel_id, self.on_restart_failed, 'dead',
            )
        # This method can be called twice, once by self.kernel_died and once
        # from the WebSocket close event. If the WebSocket connection is
        # closed before the ZMQ streams are setup, they could be None.
        for channel, stream in self.channels.items():
            if stream is not None and not stream.closed():
                stream.on_recv(None)
                # close the socket directly, don't wait for the stream
                socket = stream.socket
                stream.close()
                socket.close()
        
        self.channels = {}

    def _send_status_message(self, status):
        msg = self.session.msg("status",
            {'execution_state': status}
        )
        msg['channel'] = 'iopub'
        self.write_message(json.dumps(msg, default=date_default))

    def on_kernel_restarted(self):
        logging.warn("kernel %s restarted", self.kernel_id)
        self._send_status_message('restarting')

    def on_restart_failed(self):
        logging.error("kernel %s restarted failed!", self.kernel_id)
        self._send_status_message('dead')


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"

default_handlers = [
    (r"/api/kernels", MainKernelHandler),
    (r"/api/kernels/%s" % _kernel_id_regex, KernelHandler),
    (r"/api/kernels/%s/%s" % (_kernel_id_regex, _kernel_action_regex), KernelActionHandler),
    (r"/api/kernels/%s/channels" % _kernel_id_regex, ZMQChannelsHandler),
]
