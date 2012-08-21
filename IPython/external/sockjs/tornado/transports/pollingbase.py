# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.pollingbase
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Polling transports base
"""

from sockjs.tornado import basehandler
from sockjs.tornado.transports import base


class PollingTransportBase(basehandler.PreflightHandler, base.BaseTransportMixin):
    """Polling transport handler base class"""
    def initialize(self, server):
        super(PollingTransportBase, self).initialize(server)

        self.session = None

    def _get_session(self, session_id):
        return self.server.get_session(session_id)

    def _attach_session(self, session_id, start_heartbeat=False):
        session = self._get_session(session_id)

        if session is None:
            session = self.server.create_session(session_id)

        # Try to attach to the session
        if not session.set_handler(self, start_heartbeat):
            return False

        self.session = session

        # Verify if session is properly opened
        session.verify_state()

        return True

    def _detach(self):
        """Detach from the session"""
        if self.session:
            self.session.remove_handler(self)
            self.session = None

    def check_xsrf_cookie(self):
        pass

    def send_message(self, message):
        """Called by the session when some data is available"""
        raise NotImplementedError()

    def session_closed(self):
        """Called by the session when it was closed"""
        self._detach()

    def on_connection_close(self):
        # If connection was dropped by the client, close session.
        # In all other cases, connection will be closed by the server.
        if self.session is not None:
            self.session.close(1002, 'Connection interrupted')

        super(PollingTransportBase, self).on_connection_close()
