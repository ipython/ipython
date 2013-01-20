# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.xhr
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Xhr-Polling transport implementation
"""
import logging

from tornado.web import asynchronous

from IPython.external.sockjs.tornado import proto
from IPython.external.sockjs.tornado.transports import pollingbase


class XhrPollingTransport(pollingbase.PollingTransportBase):
    """xhr-polling transport implementation"""
    name = 'xhr'

    @asynchronous
    def post(self, session_id):
        # Start response
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()

        # Get or create session without starting heartbeat
        if not self._attach_session(session_id, False):
            return

        # Might get already detached because connection was closed in on_open
        if not self.session:
            return

        if not self.session.send_queue:
            self.session.start_heartbeat()
        else:
            self.session.flush()

    def send_pack(self, message, binary=False):
        if binary:
            raise Exception('binary not supported for XhrPollingTransport')

        self.active = False

        try:
            self.set_header('Content-Type', 'application/javascript; charset=UTF-8')
            self.set_header('Content-Length', len(message) + 1)
            self.write(message + '\n')
            self.flush(callback=self.send_complete)
        except IOError:
            # If connection dropped, make sure we close offending session instead
            # of propagating error all way up.
            self.session.delayed_close()


class XhrSendHandler(pollingbase.PollingTransportBase):
    def post(self, session_id):
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()

        session = self._get_session(session_id)

        if session is None:
            self.set_status(404)
            return

        #data = self.request.body.decode('utf-8')
        data = self.request.body
        if not data:
            self.write("Payload expected.")
            self.set_status(500)
            return

        try:
            messages = proto.json_decode(data)
        except:
            # TODO: Proper error handling
            self.write("Broken JSON encoding.")
            self.set_status(500)
            return

        try:
            session.on_messages(messages)
        except Exception:
            logging.exception('XHR incoming')
            session.close()

            self.set_status(500)
            return

        self.set_status(204)
        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
