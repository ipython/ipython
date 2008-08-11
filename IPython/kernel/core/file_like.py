# encoding: utf-8

""" File like object that redirects its write calls to a given callback."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

import sys

class FileLike(object):
    """ FileLike object that redirects all write to a callback.

        Only the write-related methods are implemented, as well as those
        required to read a StringIO.
    """
    closed = False

    def __init__(self, write_callback):
        self.write = write_callback

    def flush(self):
        """ This method is there for compatibility with other file-like
        objects.
        """
        pass

    def close(self):
        """ This method is there for compatibility with other file-like
        objects.
        """
        pass

    def writelines(self, lines):
        map(self.write, lines)

    def isatty(self):
        """ This method is there for compatibility with other file-like
        objects.
        """
        return False

    def getvalue(self):
        """ This method is there for compatibility with other file-like
        objects.
        """
        return ''

    def reset(self):
        """ This method is there for compatibility with other file-like
        objects.
        """
        pass

    def truncate(self):
        """ This method is there for compatibility with other file-like
        objects.
        """
        pass


