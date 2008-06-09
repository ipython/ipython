# encoding: utf-8

"""Support for interactive macros in IPython"""

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

    def __repr__(self):
        return 'IPython.macro.Macro(%s)' % repr(self.value)