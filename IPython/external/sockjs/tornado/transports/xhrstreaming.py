# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.xhrstreaming
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Xhr-Streaming transport implementation
"""

from tornado.web import asynchronous

from IPython.external.sockjs.tornado.transports import streamingbase


class XhrStreamingTransport(streamingbase.StreamingTransportBase):
    name = 'xhr_streaming'

    @asynchronous
    def post(self, session_id):
        # Handle cookie
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')

        # Send prelude and flush any pending messages
        self.write('h' * 2048 + '\n')
        self.flush()

        if not self._attach_session(session_id, False):
            self.finish()
            return

        if self.session:
            self.session.flush()

    def send_pack(self, message, binary=False):
        if binary:
            raise Exception('binary not supported for XhrStreamingTransport')

        self.active = False

        try:
            self.notify_sent(len(message))

            self.write(message + '\n')
            self.flush(callback=self.send_complete)
        except IOError:
            # If connection dropped, make sure we close offending session instead
            # of propagating error all way up.
            self.session.delayed_close()
            self._detach()
