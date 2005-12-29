"""Support for interactive macros in IPython"""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

class Macro:
    """Simple class to store the value of macros as strings.

    This allows us to later exec them by checking when something is an
    instance of this class."""

    def __init__(self,data):

        # store the macro value, as a single string which can be evaluated by
        # runlines()
        self.value = ''.join(data).rstrip()+'\n'

    def __str__(self):
        return self.value
