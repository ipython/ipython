#!/usr/bin/env python
"""
Contains writer for writing nbconvert output to filesystem.
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

from .files import FilesWriter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ServeWriter(FilesWriter):
    """
    Consumes nbconvert output and produces files (inherited from FilesWriter).
    Then serve the build directory containing the nbconverted files.
    """

    def serve(self, format):
        """
        Simple implementation to serve the build directory.
        """
        
        os.chdir(self.build_directory)
        httpd = HTTPServer(('127.0.0.1', 8000), SimpleHTTPRequestHandler)
        sa = httpd.socket.getsockname()
        print("Serving '" + format + "' nbconverted ipynb on http://" + sa[0] + ":" + str(sa[1]) + "/")
        print("Use Control-C to stop this server.")
        httpd.serve_forever()