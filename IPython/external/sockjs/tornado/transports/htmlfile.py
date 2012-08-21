# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.htmlfile
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    HtmlFile transport implementation.
"""

from tornado.web import asynchronous

from sockjs.tornado import proto
from sockjs.tornado.transports import streamingbase

# HTMLFILE template
HTMLFILE_HEAD = r'''
<!doctype html>
<html><head>
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
</head><body><h2>Don't panic!</h2>
  <script>
    document.domain = document.domain;
    var c = parent.%s;
    c.start();
    function p(d) {c.message(d);};
    window.onload = function() {c.stop();};
  </script>
'''.strip()
HTMLFILE_HEAD += ' ' * (1024 - len(HTMLFILE_HEAD) + 14)
HTMLFILE_HEAD += '\r\n\r\n'


class HtmlFileTransport(streamingbase.StreamingTransportBase):
    name = 'htmlfile'

    def initialize(self, server):
        super(HtmlFileTransport, self).initialize(server)

    @asynchronous
    def get(self, session_id):
        # Start response
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()
        self.set_header('Content-Type', 'text/html; charset=UTF-8')

        # Grab callback parameter
        callback = self.get_argument('c', None)
        if not callback:
            self.write('"callback" parameter required')
            self.set_status(500)
            self.finish()
            return

        # TODO: Fix me - use parameter
        self.write(HTMLFILE_HEAD % callback)
        self.flush()

        # Now try to attach to session
        if not self._attach_session(session_id):
            self.finish()
            return

        # Flush any pending messages
        if self.session:
            self.session.flush()

    def send_pack(self, message):
        # TODO: Just do escaping
        msg = '<script>\np(%s);\n</script>\r\n' % proto.json_encode(message)

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
