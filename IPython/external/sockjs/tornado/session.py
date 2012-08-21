# -*- coding: utf-8 -*-
"""
    sockjs.tornado.session
    ~~~~~~~~~~~~~~~~~~~~~~

    SockJS session implementation.
"""

import logging

from sockjs.tornado import sessioncontainer, periodic, proto


class ConnectionInfo(object):
    """Connection information object.

    Will be passed to the ``on_open`` handler of your connection class.

    Has few properties:

    `ip`
        Caller IP address
    `cookies`
        Collection of cookies
    `arguments`
        Collection of the query string arguments
    """
    def __init__(self, ip, cookies, arguments):
        self.ip = ip
        self.cookies = cookies
        self.arguments = arguments

    def get_argument(self, name):
        """Return single argument by name"""
        val = self.arguments.get(name)
        if val:
            return val[0]
        return None

    def get_cookie(self, name):
        """Return single cookie by its name"""
        return self.cookies.get(name)


# Session states
CONNECTING = 0
OPEN = 1
CLOSING = 2
CLOSED = 3


class BaseSession(object):
    """Base session implementation class"""
    def __init__(self, conn, server):
        """Base constructor.

        `conn`
            Connection class
        `server`
            SockJSRouter instance
        """
        self.server = server
        self.stats = server.stats

        self.send_expects_json = False

        self.handler = None
        self.state = CONNECTING

        self.conn_info = None

        self.conn = conn(self)

        self.close_reason = None

    def set_handler(self, handler):
        """Set transport handler
        ``handler``
            Handler, should derive from the `sockjs.tornado.transports.base.BaseTransportMixin`.
        """
        if self.handler is not None:
            raise Exception('Attempted to overwrite BaseSession handler')

        self.handler = handler
        self.transport_name = self.handler.name

        if self.conn_info is None:
            self.conn_info = handler.get_conn_info()
            self.stats.on_sess_opened(self.transport_name)

        return True

    def verify_state(self):
        """Verify if session was not yet opened. If it is, open it and call connections `on_open`"""
        if self.state == CONNECTING:
            self.state = OPEN

            self.conn.on_open(self.conn_info)

    def remove_handler(self, handler):
        """Remove active handler from the session

        `handler`
            Handler to remove
        """
        # Attempt to remove another handler
        if self.handler != handler:
            raise Exception('Attempted to remove invalid handler')

        self.handler = None

    def close(self, code=3000, message='Go away!'):
        """Close session or endpoint connection.

        `code`
            Closing code
        `message`
            Close message
        """
        if self.state != CLOSED:
            try:
                self.conn.on_close()
            except:
                logging.debug("Failed to call on_close().", exc_info=True)
            finally:
                self.state = CLOSED
                self.close_reason = (code, message)

            # Bump stats
            self.stats.on_sess_closed(self.transport_name)

            # If we have active handler, notify that session was closed
            if self.handler is not None:
                self.handler.session_closed()

    def delayed_close(self):
        """Delayed close - won't close immediately, but on next ioloop tick."""
        self.state = CLOSING
        self.server.io_loop.add_callback(self.close)

    def get_close_reason(self):
        """Return last close reason tuple.

        For example:

            if self.session.is_closed:
                code, reason = self.session.get_close_reason()

        """
        if self.close_reason:
            return self.close_reason

        return (3000, 'Go away!')

    @property
    def is_closed(self):
        """Check if session was closed."""
        return self.state == CLOSED or self.state == CLOSING

    def send_message(self, msg, stats=True):
        """Send or queue outgoing message

        `msg`
            Message to send
        `stats`
            If set to True, will update statistics after operation completes
        """
        raise NotImplemented()

    def send_jsonified(self, msg, stats=True):
        """Send or queue outgoing message which was json-encoded before. Used by the `broadcast`
        method.

        `msg`
            JSON-encoded message to send
        `stats`
            If set to True, will update statistics after operation completes
        """
        raise NotImplemented()

    def broadcast(self, clients, msg):
        """Optimized `broadcast` implementation. Depending on type of the session, will json-encode
        message once and will call either `send_message` or `send_jsonifed`.

        `clients`
            Clients iterable
        `msg`
            Message to send
        """
        self.server.broadcast(clients, msg)


class Session(BaseSession, sessioncontainer.SessionMixin):
    """SockJS session implementation.
    """

    def __init__(self, conn, server, session_id, expiry=None):
        """Session constructor.

        `conn`
            Default connection class
        `server`
            `SockJSRouter` instance
        `session_id`
            Session id
        `expiry`
            Session expiry time
        """
        # Initialize session
        sessioncontainer.SessionMixin.__init__(self, session_id, expiry)
        BaseSession.__init__(self, conn, server)

        self.send_queue = ''
        self.send_expects_json = True

        # Heartbeat related stuff
        self._heartbeat_timer = None
        self._heartbeat_interval = self.server.settings['heartbeat_delay'] * 1000

        self._immediate_flush = self.server.settings['immediate_flush']
        self._pending_flush = False

        self._verify_ip = self.server.settings['verify_ip']

    # Session callbacks
    def on_delete(self, forced):
        """Session expiration callback

        `forced`
            If session item explicitly deleted, forced will be set to True. If
            item expired, will be set to False.
        """
        # Do not remove connection if it was not forced and there's running connection
        if not forced and self.handler is not None and not self.is_closed:
            self.promote()
        else:
            self.close()

    # Add session
    def set_handler(self, handler, start_heartbeat=True):
        """Set active handler for the session

        `handler`
            Associate active Tornado handler with the session
        `start_heartbeat`
            Should session start heartbeat immediately
        """
        # Check if session already has associated handler
        if self.handler is not None:
            handler.send_pack(proto.disconnect(2010, "Another connection still open"))
            return False

        if self._verify_ip and self.conn_info is not None:
            # If IP address doesn't match - refuse connection
            if handler.request.remote_ip != self.conn_info.ip:
                logging.error('Attempted to attach to session %s (%s) from different IP (%s)' % (
                              self.session_id,
                              self.conn_info.ip,
                              handler.request.remote_ip
                              ))

                handler.send_pack(proto.disconnect(2010, "Attempted to connect to session from different IP"))
                return False

        if self.state == CLOSING or self.state == CLOSED:
            handler.send_pack(proto.disconnect(*self.get_close_reason()))
            return False

        # Associate handler and promote session
        super(Session, self).set_handler(handler)

        self.promote()

        if start_heartbeat:
            self.start_heartbeat()

        return True

    def verify_state(self):
        """Verify if session was not yet opened. If it is, open it and call connections `on_open`"""
        # If we're in CONNECTING state - send 'o' message to the client
        if self.state == CONNECTING:
            self.handler.send_pack(proto.CONNECT)

        # Call parent implementation
        super(Session, self).verify_state()

    def remove_handler(self, handler):
        """Detach active handler from the session

        `handler`
            Handler to remove
        """
        super(Session, self).remove_handler(handler)

        self.promote()
        self.stop_heartbeat()

    def send_message(self, msg, stats=True):
        """Send or queue outgoing message

        `msg`
            Message to send
        `stats`
            If set to True, will update statistics after operation completes
        """
        self.send_jsonified(proto.json_encode(msg), stats)

    def send_jsonified(self, msg, stats=True):
        """Send JSON-encoded message

        `msg`
            JSON encoded string to send
        `stats`
            If set to True, will update statistics after operation completes
        """
        assert isinstance(msg, basestring), 'Can only send strings'

        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')

        if self._immediate_flush:
            if self.handler and not self.send_queue:
                # Send message right away
                self.handler.send_pack('a[%s]' % msg)
            else:
                if self.send_queue:
                    self.send_queue += ','
                self.send_queue += msg

                self.flush()
        else:
            if self.send_queue:
                self.send_queue += ','
            self.send_queue += msg

            if not self._pending_flush:
                self.server.io_loop.add_callback(self.flush)
                self._pending_flush = True

        if stats:
            self.stats.on_pack_sent(1)

    def flush(self):
        """Flush message queue if there's an active connection running"""
        self._pending_flush = False

        if self.handler is None:
            return

        if not self.send_queue:
            return

        self.handler.send_pack('a[%s]' % self.send_queue)
        self.send_queue = ''

    def close(self, code=3000, message='Go away!'):
        """Close session.

        `code`
            Closing code
        `message`
            Closing message
        """
        if self.state != CLOSED:
            # Notify handler
            if self.handler is not None:
                self.handler.send_pack(proto.disconnect(code, message))

        super(Session, self).close(code, message)

    # Heartbeats
    def start_heartbeat(self):
        """Reset hearbeat timer"""
        self.stop_heartbeat()

        self._heartbeat_timer = periodic.Callback(self._heartbeat,
                                                  self._heartbeat_interval,
                                                  self.server.io_loop)
        self._heartbeat_timer.start()

    def stop_heartbeat(self):
        """Stop active heartbeat"""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.stop()
            self._heartbeat_timer = None

    def delay_heartbeat(self):
        """Delay active heartbeat"""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.delay()

    def _heartbeat(self):
        """Heartbeat callback"""
        if self.handler is not None:
            self.handler.send_pack(proto.HEARTBEAT)
        else:
            self.stop_heartbeat()

    def on_messages(self, msg_list):
        """Handle incoming messages

        `msg_list`
            Message list to process
        """
        self.stats.on_pack_recv(len(msg_list))

        for msg in msg_list:
            self.conn.on_message(msg)
