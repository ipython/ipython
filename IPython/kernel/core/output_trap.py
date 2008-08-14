# encoding: utf-8

""" Trap stdout/stderr."""

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
from cStringIO import StringIO


class OutputTrap(object):
    """ Object which can trap text sent to stdout and stderr.
    """

    def __init__(self, out=None, err=None):
        # Filelike objects to store stdout/stderr text.
        if out is None:
            self.out = StringIO()
        else:
            self.out = out
        if err is None:
            self.err = StringIO()
        else:
            self.err = err

        # Boolean to check if the stdout/stderr hook is set.
        self.out_set = False
        self.err_set = False

    @property
    def out_text(self):
        """ Return the text currently in the stdout buffer.
        """
        return self.out.getvalue()

    @property
    def err_text(self):
        """ Return the text currently in the stderr buffer.
        """
        return self.err.getvalue()

    def set(self):
        """ Set the hooks.
        """

        if sys.stdout is not self.out:
            self._out_save = sys.stdout
            sys.stdout = self.out
            self.out_set = True

        if sys.stderr is not self.err:
            self._err_save = sys.stderr
            sys.stderr = self.err
            self.err_set = True

    def unset(self):
        """ Remove the hooks.
        """

        if self.out_set:
            sys.stdout = self._out_save
        self.out_set = False

        if self.err_set:
            sys.stderr = self._err_save
        self.err_set = False

    def clear(self):
        """ Clear out the buffers.
        """

        self.out.reset()
        self.out.truncate()

        self.err.reset()
        self.err.truncate()

    def add_to_message(self, message):
        """ Add the text from stdout and stderr to the message from the
        interpreter to its listeners.

        Parameters
        ----------
        message : dict
        """

        out_text = self.out_text
        if out_text:
            message['stdout'] = out_text

        err_text = self.err_text
        if err_text:
            message['stderr'] = err_text



