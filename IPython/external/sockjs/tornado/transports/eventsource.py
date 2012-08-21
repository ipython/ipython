# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.eventsource
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    EventSource transport implementation.
"""

from tornado.web import asynchronous

from sockjs.tornado.transports import streamingbase


class EventSourceTransport(streamingbase.StreamingTransportBase):
    name = 'eventsource'

    @asynchronous
    def get(self, session_id):
        # Start response
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()

        self.set_header('Content-Type', 'text/event-stream; charset=UTF-8')
        self.write('\r\n')
        self.flush()

        if not self._attach_session(session_id):
            self.finish()
            return

        if self.session:
            self.session.flush()

    def send_pack(self, message):
        msg = 'data: %s\r\n\r\n' % message

        try:
            self.write(msg)
            self.flush()
        except IOError:
            # If connection dropped, make sure we close offending session instead
            # of propagating error all way up.
            self.session.delayed_close()
            self._detach()

        # Close connection based on amount of data transferred
        if self.should_finish(len(msg)):
            self._detach()
            self.safe_finish()
