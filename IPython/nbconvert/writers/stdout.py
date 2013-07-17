#!/usr/bin/env python
"""
Contains Stdout writer
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

from .base import WriterBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class StdoutWriter(WriterBase):
    """Consumes output from nbconvert export...() methods and writes to the 
    stdout stream.  Allows for quick debuging of nbconvert output.  Using the
    debug flag makes the writer pretty-print the figures contained within the
    notebook."""


    def write(self, output, resources, **kw):
        """
        Consume and write Jinja output.

        See base for more...
        """

        print(output)
