"""
Contains postprocessor for serving nbconvert output.
"""
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

from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from IPython.utils.traitlets import Bool

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ServePostProcessor(PostProcessorBase):
    """Post processor designed to serve files"""


    open_in_browser = Bool(True, config=True,
                           help="""Set to False to deactivate
                           the opening of the browser""")

    def call(self, input):
        """
        Simple implementation to serve the build directory.
        """

        try:
            dirname, filename = os.path.split(input)
            if dirname:
                os.chdir(dirname)
            httpd = HTTPServer(('127.0.0.1', 8000), SimpleHTTPRequestHandler)
            sa = httpd.socket.getsockname()
            url = "http://" + sa[0] + ":" + str(sa[1]) + "/" + filename
            if self.open_in_browser:
                webbrowser.open(url, new=2)
            print("Serving your slides on " + url)
            print("Use Control-C to stop this server.")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("The server is shut down.")
