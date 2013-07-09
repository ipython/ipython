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

import logging
from tornado import web

from zmq.utils import jsonapi

from IPython.utils.jsonutil import date_default

from ...base.handlers import IPythonHandler
from ...base.zmqhandlers import AuthenticatedZMQStreamHandler

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


class ZMQChannelHandler(AuthenticatedZMQStreamHandler):
    
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
