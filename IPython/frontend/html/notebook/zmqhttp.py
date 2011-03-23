import json

from tornado import web

import logging


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


class ZMQXReqHandler(ZMQHandler):

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




    