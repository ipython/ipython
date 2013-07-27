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
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from IPython.utils.traitlets import Unicode

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ServePostProcessor(PostProcessorBase):
    """Post processor designed to serve files"""


    build_directory = Unicode(".", config=True, 
                              help="""Directory to write output to.  Leave blank
                              to output to the current directory""")

    def call(self, input):
        """
        Simple implementation to serve the build directory.
        """
        
        os.chdir(self.build_directory)
        httpd = HTTPServer(('127.0.0.1', 8000), SimpleHTTPRequestHandler)
        sa = httpd.socket.getsockname()
        print("Serving '" + input + "' nbconverted from ipynb on http://" + sa[0] + ":" + str(sa[1]) + "/")
        print("Use Control-C to stop this server.")
        httpd.serve_forever()
