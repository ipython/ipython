"""PostProcessor for serving reveal.js HTML slideshows."""
from __future__ import print_function
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import webbrowser

from tornado import web, ioloop, httpserver
from tornado.httpclient import AsyncHTTPClient

from IPython.utils.traitlets import Bool, Unicode, Int

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ProxyHandler(web.RequestHandler):
    """handler the proxies requests from a local prefix to a CDN"""
    @web.asynchronous
    def get(self, prefix, url):
        """proxy a request to a CDN"""
        proxy_url = "/".join([self.settings['cdn'], url])
        client = self.settings['client']
        client.fetch(proxy_url, callback=self.finish_get)
    
    def finish_get(self, response):
        """finish the request"""
        # copy potentially relevant headers
        for header in ["Content-Type", "Cache-Control", "Date", "Last-Modified", "Expires"]:
            if header in response.headers:
                self.set_header(header, response.headers[header])
        self.finish(response.body)

class ServePostProcessor(PostProcessorBase):
    """Post processor designed to serve files
    
    Proxies reveal.js requests to a CDN if no local reveal.js is present
    """


    open_in_browser = Bool(True, config=True,
        help="""Should the browser be opened automatically?"""
    )
    reveal_cdn = Unicode("https://cdn.jsdelivr.net/reveal.js/2.5.0", config=True,
        help="""URL for reveal.js CDN."""
    )
    reveal_prefix = Unicode("reveal.js", config=True, help="URL prefix for reveal.js")
    ip = Unicode("127.0.0.1", config=True, help="The IP address to listen on.")
    port = Int(8000, config=True, help="port for the server to listen on.")

    def postprocess(self, input):
        """Serve the build directory with a webserver."""
        dirname, filename = os.path.split(input)
        handlers = [
            (r"/(.+)", web.StaticFileHandler, {'path' : dirname}),
            (r"/", web.RedirectHandler, {"url": "/%s" % filename})
        ]
        
        if ('://' in self.reveal_prefix or self.reveal_prefix.startswith("//")):
            # reveal specifically from CDN, nothing to do
            pass
        elif os.path.isdir(os.path.join(dirname, self.reveal_prefix)):
            # reveal prefix exists
            self.log.info("Serving local %s", self.reveal_prefix)
        else:
            self.log.info("Redirecting %s requests to %s", self.reveal_prefix, self.reveal_cdn)
            handlers.insert(0, (r"/(%s)/(.*)" % self.reveal_prefix, ProxyHandler))
        
        app = web.Application(handlers,
            cdn=self.reveal_cdn,
            client=AsyncHTTPClient(),
        )
        # hook up tornado logging to our logger
        try:
            from tornado import log
            log.app_log = self.log
        except ImportError:
            # old tornado (<= 3), ignore
            pass
    
        http_server = httpserver.HTTPServer(app)
        http_server.listen(self.port, address=self.ip)
        url = "http://%s:%i/%s" % (self.ip, self.port, filename)
        print("Serving your slides at %s" % url)
        print("Use Control-C to stop this server")
        if self.open_in_browser:
            webbrowser.open(url, new=2)
        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            print("\nInterrupted")

def main(path):
    """allow running this module to serve the slides"""
    server = ServePostProcessor()
    server(path)
    
if __name__ == '__main__':
    import sys
    main(sys.argv[1])
