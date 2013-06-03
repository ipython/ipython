"""
Shim to maintain backwards compatibility with old frontend imports.

We have moved all contents of the old `frontend` subpackage into top-level
subpackages (`html`, `qt` and `terminal`).  This will let code that was making
`from IPython.frontend...` calls continue working, though a warning will be
printed.
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2013, IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function
import sys
import types

#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------

class ShimModule(types.ModuleType):

    def __getattribute__(self, key):
        m = ("*** WARNING*** : The top-level `frontend` module has been deprecated.\n"
        "Please import %s directly from the `IPython` level." % key)

        # FIXME: I don't understand why, but if the print statement below is
        # redirected to stderr, this shim module stops working.  It seems the
        # Python import machinery has problem with redirected prints happening
        # during the import process.  If we can't figure out a solution, we may
        # need to leave it to print to default stdout.
        print(m)
        
        # FIXME: this seems to work fine, but we should replace it with an
        # __import__ call instead of using exec/eval.
        exec 'from IPython import %s' % key
        return eval(key)


# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.frontend'] = ShimModule('frontend')
