from IPython.external.sockjs.tornado.transports import pollingbase


class StreamingTransportBase(pollingbase.PollingTransportBase):
    def initialize(self, server):
        super(StreamingTransportBase, self).initialize(server)

        self.amount_limit = self.server.settings['response_limit']

        # HTTP 1.0 client might send keep-alive
        if hasattr(self.request, 'connection') and not self.request.supports_http_1_1():
            self.request.connection.no_keep_alive = True

    def notify_sent(self, data_len):
        """
            Update amount of data sent
        """
        self.amount_limit -= data_len

    def should_finish(self):
        """
            Check if transport should close long running connection after
            sending X bytes to the client.

            `data_len`
                Amount of data that was sent
        """
        if self.amount_limit <= 0:
            return True

        return False

    def send_complete(self):
        """
            Verify if connection should be closed based on amount of data that was sent.
        """
        self.active = True

        if self.should_finish():
            self._detach()
            self.safe_finish()
        else:
            if self.session:
                self.session.flush()
