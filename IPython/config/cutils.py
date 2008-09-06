# encoding: utf-8

"""Configuration-related utilities for all IPython."""

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

import os
import sys

#---------------------------------------------------------------------------
# Normal code begins
#---------------------------------------------------------------------------

def import_item(key):
    """
    Import and return bar given the string foo.bar.
    """
    package = '.'.join(key.split('.')[0:-1])
    obj = key.split('.')[-1]
    execString = 'from %s import %s' % (package, obj)
    exec execString
    exec 'temp = %s' % obj 
    return temp
