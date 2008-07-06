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

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Ville']
__license__ = Release.license

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

def freeze_term_title():
    _platutils.ignore_termtitle = True


def set_term_title(title):
    """Set terminal title using the necessary platform-dependent calls."""

    if _platutils.ignore_termtitle:
        return
    _platutils.set_term_title(title)
