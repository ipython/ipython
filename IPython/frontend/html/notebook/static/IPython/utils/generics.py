# encoding: utf-8
"""Generic functions for extending IPython.

See http://cheeseshop.python.org/pypi/simplegeneric.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.error import TryNext
from IPython.external.simplegeneric import generic

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


@generic
def inspect_object(obj):
    """Called when you do obj?"""
    raise TryNext


@generic
def complete_object(obj, prev_completions):
    """Custom completer dispatching for python objects.

    Parameters
    ----------
    obj : object
        The object to complete.
    prev_completions : list
        List of attributes discovered so far.

    This should return the list of attributes in obj. If you only wish to
    add to the attributes already discovered normally, return
    own_attrs + prev_completions.
    """
    raise TryNext


