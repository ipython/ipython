"""
Shim to maintain backwards compatibility with old frontend imports.

We have moved all contents of the old `frontend` subpackage into top-level
subpackages (`html`, `qt` and `terminal`).  

This will let code that was making `from IPython.frontend...` calls continue
working, though a warning will be printed.
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

# Stdlib
import sys
import types
from warnings import warn

warn("The top-level `frontend` package has been deprecated. "
     "All its subpackages have been moved to the top `IPython` level.")

#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------

class ShimModule(types.ModuleType):
    
    def __init__(self, *args, **kwargs):
        self._mirror = kwargs.pop("mirror")
        super(ShimModule, self).__init__(*args, **kwargs)

    def __getattr__(self, key):
        # Use the equivalent of import_item(name), see below
        name = "%s.%s" % (self._mirror, key)

        # NOTE: the code below is copied *verbatim* from
        # importstring.import_item. For some very strange reason that makes no
        # sense to me, if we call it *as a function*, it doesn't work.  This
        # has something to do with the deep bowels of the import machinery and
        # I couldn't find a way to make the code work as a standard function
        # call.  But at least since it's an unmodified copy of import_item,
        # which is used extensively and has a test suite, we can be reasonably
        # confident this is OK.  If anyone finds how to call the function, all
        # the below could be replaced simply with:
        #
        # from IPython.utils.importstring import import_item
        # return import_item('MIRROR.' + key)
        
        parts = name.rsplit('.', 1)
        if len(parts) == 2:
            # called with 'foo.bar....'
            package, obj = parts
            module = __import__(package, fromlist=[obj])
            try:
                pak = module.__dict__[obj]
            except KeyError:
                raise ImportError('No module named %s' % obj)
            return pak
        else:
            # called with un-dotted string
            return __import__(parts[0])


# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.frontend.html.notebook'] = ShimModule('notebook', mirror='IPython.html')
sys.modules['IPython.frontend'] = ShimModule('frontend', mirror='IPython')
