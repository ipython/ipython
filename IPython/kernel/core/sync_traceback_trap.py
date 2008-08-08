# encoding: utf-8

"""Object to manage sys.excepthook().

Synchronous version: prints errors when called.
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
from traceback_trap import TracebackTrap
from IPython.ultraTB import ColorTB

class SyncTracebackTrap(TracebackTrap):

    def __init__(self, sync_formatter=None, formatters=None):
        TracebackTrap.__init__(self, formatters=formatters)
        if sync_formatter is None:
            sync_formatter = ColorTB(color_scheme='LightBG')
        self.sync_formatter = sync_formatter


    def hook(self, *args):
        """ This method actually implements the hook.
        """
        self.args = args
        
        print self.sync_formatter(*self.args)


        

