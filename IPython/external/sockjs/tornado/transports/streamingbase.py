from sockjs.tornado.transports import pollingbase


class StreamingTransportBase(pollingbase.PollingTransportBase):
    def initialize(self, server):
        super(StreamingTransportBase, self).initialize(server)

        self.amount_limit = self.server.settings['response_limit']

        # HTTP 1.0 client might send keep-alive
        if hasattr(self.request, 'connection') and not self.request.supports_http_1_1():
            self.request.connection.no_keep_alive = True

    def should_finish(self, data_len):
        """Check if transport should close long running connection after
        sending X bytes to the client.

        `data_len`
            Amount of data that was sent
        """
        self.amount_limit -= data_len

        if self.amount_limit <= 0:
            return True

    def session_closed(self):
        """Called by the session when it was closed"""
        self._detach()

        self.safe_finish()
