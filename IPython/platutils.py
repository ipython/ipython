# -*- coding: utf-8 -*-
""" Proxy module for accessing platform specific utility functions. 

Importing this module should give you the implementations that are correct 
for your operation system, from platutils_PLATFORMNAME module.

$Id: ipstruct.py 1005 2006-01-12 08:39:26Z fperez $


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

import os,sys

if os.name == 'posix':
    from platutils_posix import *
elif sys.platform == 'win32':
    from platutils_win32 import *
else:
    from platutils_dummy import *
    import warnings
    warnings.warn("Platutils not available for platform '%s', some features may be missing" %
        os.name)
    del warnings
