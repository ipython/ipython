"""Support for interactive macros in IPython"""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import IPython.ipapi 


from IPython.genutils import Term
from IPython.ipapi import IPyAutocall

class Macro(IPyAutocall):
    """Simple class to store the value of macros as strings.

    Macro is just a callable that executes a string of IPython
    input when called.
    """

    def __init__(self,data):

        # store the macro value, as a single string which can be evaluated by
        # runlines()
        self.value = ''.join(data).rstrip()+'\n'
        
    def __str__(self):
        return self.value

    def __repr__(self):
        return 'IPython.macro.Macro(%s)' % repr(self.value)
    
    def __call__(self):
        Term.cout.flush()
        
        self._ip.runlines(self.value)