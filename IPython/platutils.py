# -*- coding: utf-8 -*-
""" Proxy module for accessing platform specific utility functions. 

Importing this module should give you the implementations that are correct 
for your operation system, from platutils_PLATFORMNAME module.
"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import os
import sys

# Import the platform-specific implementations
if os.name == 'posix':
    import platutils_posix as _platutils
elif sys.platform == 'win32':
    import platutils_win32 as _platutils
else:
    import platutils_dummy as _platutils
    import warnings
    warnings.warn("Platutils not available for platform '%s', some features may be missing" %
        os.name)
    del warnings


# Functionality that's logically common to all platforms goes here, each
# platform-specific module only provides the bits that are OS-dependent.

# XXX - I'm still not happy with a module global for this, but at least now
# there is a public, cross-platform way of toggling the term title control on
# and off.  We should make this a stateful object later on so that each user
# can have its own instance if needed.
def toggle_set_term_title(val):
    """Control whether set_term_title is active or not.

    set_term_title() allows writing to the console titlebar.  In embedded
    widgets this can cause problems, so this call can be used to toggle it on
    or off as needed.

    The default state of the module is for the function to be disabled.

    Parameters
    ----------
      val : bool
        If True, set_term_title() actually writes to the terminal (using the
        appropriate platform-specific module).  If False, it is a no-op.
    """
    _platutils.ignore_termtitle = not(val)


def set_term_title(title):
    """Set terminal title using the necessary platform-dependent calls."""

    if _platutils.ignore_termtitle:
        return
    _platutils.set_term_title(title)


#-----------------------------------------------------------------------------
# Deprecated functions
#-----------------------------------------------------------------------------
def freeze_term_title():
    warnings.warn("This function is deprecated, use toggle_set_term_title()")
    _platutils.ignore_termtitle = True

