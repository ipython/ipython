# encoding: utf-8

""" Redirects stdout/stderr to given write methods."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys
from IPython.kernel.core.output_trap import OutputTrap 

class FileLike(object):
    """ FileLike object that redirects all write to a callback.

        Only the write-related methods are implemented, as well as those
        required to read a StringIO.
    """
    closed = False

    def __init__(self, write):
        self.write = write

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


class SyncOutputTrap(OutputTrap):
    """ Object which redirect text sent to stdout and stderr to write
        callbacks.
    """
    
    def __init__(self, write_out, write_err):
        # Store callbacks
        self.out = FileLike(write_out)
        self.err = FileLike(write_err)

        # Boolean to check if the stdout/stderr hook is set.
        self.out_set = False
        self.err_set = False

    def clear(self):
        """ Clear out the buffers.
        """
        pass

