# -*- coding: utf-8 -*-
"""
    sockjs.tornado.migrate
    ~~~~~~~~~~~~~~~~~~~~~~

    `tornado.websocket` to `sockjs.tornado` migration helper.
"""

from sockjs.tornado import conn


class WebsocketHandler(conn.SockJSConnection):
    """If you already use Tornado websockets for your application and
    want try sockjs-tornado, change your handlers to derive from this
    WebsocketHandler class. There are some limitations, for example
    only self.request only contains remote_ip, cookies and arguments
    collection"""
    def open(self):
        """open handler"""
        pass

    def on_open(self, info):
        """sockjs-tornado on_open handler"""
        # Store some properties
        self.remote_ip = info.remote_ip

        # Create fake request object
        self.request = info

        # Call open
        self.open()

    def write_message(self, msg):
        self.send(msg)
