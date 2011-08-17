"""Base classes and utilities for readers and writers.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from base64 import encodestring, decodestring
import pprint

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def base64_decode(nb):
    """Base64 encode all bytes objects in the notebook."""
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                if 'png' in cell:
                    cell.png = bytes(decodestring(cell.png))
                if 'jpeg' in cell:
                    cell.jpeg = bytes(decodestring(cell.jpeg))
    return nb


def base64_encode(nb):
    """Base64 decode all binary objects in the notebook."""
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                if 'png' in cell:
                    cell.png = unicode(encodestring(cell.png))
                if 'jpeg' in cell:
                    cell.jpeg = unicode(encodestring(cell.jpeg))
    return nb


class NotebookReader(object):
    """A class for reading notebooks."""

    def reads(self, s, **kwargs):
        """Read a notebook from a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def read(self, fp, **kwargs):
        """Read a notebook from a file like object"""
        return self.read(fp.read(), **kwargs)


class NotebookWriter(object):
    """A class for writing notebooks."""

    def writes(self, nb, **kwargs):
        """Write a notebook to a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def write(self, nb, fp, **kwargs):
        """Write a notebook to a file like object"""
        return fp.write(self.writes(nb,**kwargs))



