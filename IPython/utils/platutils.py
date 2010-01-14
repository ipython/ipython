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
import warnings

# Import the platform-specific implementations
if os.name == 'posix':
    import platutils_posix as _platutils
elif sys.platform == 'win32':
    import platutils_win32 as _platutils
else:
    import platutils_dummy as _platutils

# Functionality that's logically common to all platforms goes here, each
# platform-specific module only provides the bits that are OS-dependent.

# XXX - I'm still not happy with a module global for this, but at least now
# there is a public, cross-platform way of toggling the term title control on
# and off.  We should make this a stateful object later on so that each user
# can have its own instance if needed.
def term_clear():
    _platutils.term_clear()

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


class FindCmdError(Exception):
    pass

def find_cmd(cmd):
    """Find full path to executable cmd in a cross platform manner.
    
    This function tries to determine the full path to a command line program
    using `which` on Unix/Linux/OS X and `win32api` on Windows.  Most of the
    time it will use the version that is first on the users `PATH`.  If
    cmd is `python` return `sys.executable`.

    Parameters
    ----------
    cmd : str
        The command line program to look for.
    """
    if cmd == 'python':
        return sys.executable
    try:
        path = _platutils.find_cmd(cmd)
    except OSError:
        raise FindCmdError('command could not be found: %s' % cmd)
    # which returns empty if not found
    if path == '':
        raise FindCmdError('command could not be found: %s' % cmd)
    return path

def get_long_path_name(path):
    """Expand a path into its long form.

    On Windows this expands any ~ in the paths. On other platforms, it is
    a null operation.
    """
    return _platutils.get_long_path_name(path)

#-----------------------------------------------------------------------------
# Deprecated functions
#-----------------------------------------------------------------------------
def freeze_term_title():
    warnings.warn("This function is deprecated, use toggle_set_term_title()")
    _platutils.ignore_termtitle = True
