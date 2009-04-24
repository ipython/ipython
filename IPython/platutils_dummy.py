# -*- coding: utf-8 -*-
""" Platform specific utility functions, dummy version 

This has empty implementation of the platutils functions, used for 
unsupported operating systems.

Authors
-------
- Ville Vainio <vivainio@gmail.com>
"""

#*****************************************************************************
#       Copyright (C) 2008-2009 The IPython Development Team
#       Copyright (C) 2001-2007 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# This variable is part of the expected API of the module:
ignore_termtitle = True

def set_term_title(*args,**kw):
    """Dummy no-op."""
    pass

def find_cmd(cmd):
    """Find the full path to a command using which."""
    return os.popen('which %s' % cmd).read().strip()
