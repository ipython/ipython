# -*- coding: utf-8 -*-
"""
    sockjs.tornado.router
    ~~~~~~~~~~~~~~~~~~~~~

    SockJS protocol router implementation.
"""

from tornado import ioloop, version_info

from sockjs.tornado import transports, session, sessioncontainer, static, stats, proto


DEFAULT_SETTINGS = {
    # Sessions check interval in seconds
    'session_check_interval': 1,
    # Session expiration in seconds
    'disconnect_delay': 5,
    # Heartbeat time in seconds. Do not change this value unless
    # you absolutely sure that new value will work.
    'heartbeat_delay': 25,
    # Enabled protocols
    'disabled_transports': [],
    # SockJS location
    'sockjs_url': 'http://cdn.sockjs.org/sockjs-0.3.min.js',
    # Max response body size
    'response_limit': 128 * 1024,
    # Enable or disable JSESSIONID cookie handling
    'jsessionid': True,
    # Should sockjs-tornado flush messages immediately or queue then and
    # flush on next ioloop tick
    'immediate_flush': True,
    # Enable or disable Nagle for persistent transports
    'disable_nagle': True,
    # Enable IP checks for polling transports. If enabled, all subsequent
    # polling calls should be from the same IP address.
    'verify_ip': True
    }

GLOBAL_HANDLERS = [
    ('xhr_send', transports.XhrSendHandler),
    ('jsonp_send', transports.JSONPSendHandler)
]

TRANSPORTS = {
    'websocket': transports.WebSocketTransport,
    'xhr': transports.XhrPollingTransport,
    'xhr_streaming': transports.XhrStreamingTransport,
    'jsonp': transports.JSONPTransport,
    'eventsource': transports.EventSourceTransport,
    'htmlfile': transports.HtmlFileTransport
}

STATIC_HANDLERS = {
    '/chunking_test': static.ChunkingTestHandler,
    '/info': static.InfoHandler,
    '/iframe[0-9-.a-z_]*.html': static.IFrameHandler,
    '/websocket': transports.RawWebSocketTransport,
    '/?': static.GreetingsHandler
}


class SockJSRouter(object):
    """SockJS protocol router"""
    def __init__(self,
                 connection,
                 prefix='',
                 user_settings=dict(),
                 io_loop=None):
        """Constructor.

        `connection`
            SockJSConnection class
        `prefix`
            Connection prefix
        `user_settings`
            Settings dictionary
        `io_loop`
            Optional IOLoop instance
        """

        # TODO: Version check
        if version_info[0] < 2:
            raise Exception('sockjs-tornado requires Tornado 2.0 or higher.')

        # Store connection class
        self._connection = connection

        # Initialize io_loop
        self.io_loop = io_loop or ioloop.IOLoop.instance()

        # Settings
        self.settings = DEFAULT_SETTINGS.copy()
        if user_settings:
            self.settings.update(user_settings)

        self.websockets_enabled = 'websocket' not in self.settings['disabled_transports']
        self.cookie_needed = self.settings['jsessionid']

        # Sessions
        self._sessions = sessioncontainer.SessionContainer()

        check_interval = self.settings['session_check_interval'] * 1000
        self._sessions_cleanup = ioloop.PeriodicCallback(self._sessions.expire,
                                                         check_interval,
                                                         self.io_loop)
        self._sessions_cleanup.start()

        # Stats
        self.stats = stats.StatsCollector(self.io_loop)

        # Initialize URLs
        base = prefix + r'/[^/.]+/(?P<session_id>[^/.]+)'

        # Generate global handler URLs
        self._transport_urls = [('%s/%s$' % (base, p[0]), p[1], dict(server=self))
                                for p in GLOBAL_HANDLERS]

        for k, v in TRANSPORTS.iteritems():
            if k in self.settings['disabled_transports']:
                continue

            # Only version 1 is supported
            self._transport_urls.append(
                (r'%s/%s$' % (base, k),
                 v,
                 dict(server=self))
                )

        # Generate static URLs
        map(self._transport_urls.append,
            (('%s%s' % (prefix, k), v, dict(server=self))
            for k, v in STATIC_HANDLERS.iteritems()))

    @property
    def urls(self):
        """List of the URLs to be added to the Tornado application"""
        return self._transport_urls

    def apply_routes(self, routes):
        """Feed list of the URLs to the routes list. Returns list"""
        routes.extend(self._transport_urls)
        return routes

    def create_session(self, session_id, register=True):
        """Creates new session object and returns it.

        `request`
            Request that created the session. Will be used to get query string
            parameters and cookies
        `register`
            Should be session registered in a storage. Websockets don't
            need it.
        """
        # TODO: Possible optimization here for settings.get
        s = session.Session(self._connection,
                            self,
                            session_id,
                            self.settings.get('disconnect_delay')
                            )

        if register:
            self._sessions.add(s)

        return s

    def get_session(self, session_id):
        """Get session by session id

        `session_id`
            Session id
        """
        return self._sessions.get(session_id)

    def get_connection_class(self):
        """Return associated connection class"""
        return self._connection

    # Broadcast helper
    def broadcast(self, clients, msg):
        """Optimized `broadcast` implementation. Depending on type of the session, will json-encode
        message once and will call either `send_message` or `send_jsonifed`.

        `clients`
            Clients iterable
        `msg`
            Message to send
        """
        json_msg = None

        count = 0

        for c in clients:
            sess = c.session
            if not sess.is_closed:
                if sess.send_expects_json:
                    if json_msg is None:
                        json_msg = proto.json_encode(msg)
                    sess.send_jsonified(json_msg, False)
                else:
                    sess.send_message(msg, False)

                count += 1

        self.stats.on_pack_sent(count)
