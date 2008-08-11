# encoding: utf-8

""" 
Trap stdout/stderr, including at the OS level. Calls a callback with
the output each time Python tries to write to the stdout or stderr.
"""

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

from fd_redirector import FDRedirector, STDOUT, STDERR

from IPython.kernel.core.file_like import FileLike
from IPython.kernel.core.output_trap import OutputTrap

class RedirectorOutputTrap(OutputTrap):
    """ Object which can trap text sent to stdout and stderr.
    """

    #------------------------------------------------------------------------
    # OutputTrap interface.
    #------------------------------------------------------------------------
    def __init__(self, out_callback, err_callback):
        """ 
        out_callback : callable called when there is output in the stdout
        err_callback : callable called when there is output in the stderr
        """
        # Callback invoked on write to stdout and stderr 
        self.out_callback = out_callback
        self.err_callback = err_callback

        # File descriptor redirectors, to capture non-Python
        # output.
        self.out_redirector = FDRedirector(STDOUT)
        self.err_redirector = FDRedirector(STDERR)

        # Call the base class with file like objects that will trigger
        # our callbacks
        OutputTrap.__init__(self, out=FileLike(self.on_out_write),
                                  err=FileLike(self.on_err_write), )


    def set(self):
        """ Set the hooks: set the redirectors and call the base class.
        """
        self.out_redirector.start()
        self.err_redirector.start()
        OutputTrap.set(self)


    def unset(self):
        """ Remove the hooks: call the base class and stop the
            redirectors.
        """
        OutputTrap.unset(self)
        # Flush the redirectors before stopping them
        self.on_err_write('')
        self.err_redirector.stop()
        self.on_out_write('')
        self.out_redirector.stop()


    #------------------------------------------------------------------------
    # Callbacks for synchronous output 
    #------------------------------------------------------------------------
    def on_out_write(self, string):
        """ Callback called when there is some Python output on stdout.
        """
        try:
            self.out_callback(self.out_redirector.getvalue() + string)
        except:
            # If tracebacks are happening and we can't see them, it is
            # quasy impossible to debug
            self.unset()
            raise

    def on_err_write(self, string):
        """ Callback called when there is some Python output on stderr.
        """
        try:
            self.err_callback(self.err_redirector.getvalue() + string)
        except:
            # If tracebacks are happening and we can't see them, it is
            # quasy impossible to debug
            self.unset()
            raise

