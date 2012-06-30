"""Unfinished code for ZMQ/HTTP bridging. We use WebSockets instead.

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

import json
import logging

from tornado import web

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class ZMQHandler(web.RequestHandler):

    def get_stream(self):
        """Get the ZMQStream for this request."""
        raise NotImplementedError('Implement get_stream() in a subclass.')

    def _save_method_args(self, *args, **kwargs):
        """Save the args and kwargs to get/post/put/delete for future use.

        These arguments are not saved in the request or handler objects, but
        are often needed by methods such as get_stream().
        """ 
        self._method_args = args
        self._method_kwargs = kwargs

    def _handle_msgs(self, msg):
        msgs = [msg]
        stream = self.get_stream()
        stream.on_recv(lambda m: msgs.append(json.loads(m)))
        stream.flush()
        stream.stop_on_recv()
        logging.info("Reply: %r" % msgs)
        self.write(json.dumps(msgs))
        self.finish()


class ZMQPubHandler(ZMQHandler):

    SUPPORTED_METHODS = ("POST",)

    def post(self, *args, **kwargs):
        self._save_method_args(*args, **kwargs)
        try:
            msg = json.loads(self.request.body)
        except:
            self.send_error(status_code=415)
        else:
            logging.info("Request: %r" % msg)
            self.get_stream().send_json(msg)


class ZMQSubHandler(ZMQHandler):

    SUPPORTED_METHODS = ("GET",)

    @web.asynchronous
    def get(self, *args, **kwargs):
        self._save_method_args(*args, **kwargs)
        self.get_stream().on_recv(self._handle_msgs)


class ZMQDealerHandler(ZMQHandler):

    SUPPORTED_METHODS = ("POST",)

    @web.asynchronous
    def post(self, *args, **kwargs):
        self._save_method_args(*args, **kwargs)
        logging.info("request: %r" % self.request)
        try:
            msg = json.loads(self.request.body)
        except:
            self.send_error(status_code=415)
        else:
            logging.info("Reply: %r" % msg)
            stream = self.get_stream()
            stream.send_json(msg)
            stream.on_recv(self._handle_msgs)

