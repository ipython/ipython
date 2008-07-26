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
        pass

    def close(self):
        pass

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def isatty(self):
        return False

    def getvalue(self):
        return ''

    def reset(self):
        pass

    def truncate(self):
        pass


