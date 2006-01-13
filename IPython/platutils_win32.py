# -*- coding: utf-8 -*-
""" Platform specific utility functions, win32 version

Importing this module directly is not portable - rather, import platutils 
to use these functions in platform agnostic fashion.

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


def set_term_title(title):
    """ TBD """
