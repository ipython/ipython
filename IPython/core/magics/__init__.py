"""Implementation of all the magic functions built into IPython.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.magic import Magics, register_magics
from basic import BasicMagics
from history import HistoryMagics

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@register_magics
class UserMagics(Magics):
    """Placeholder for user-defined magics to be added at runtime.

    All magics are eventually merged into a single namespace at runtime, but we
    use this class to isolate the magics defined dynamically by the user into
    their own class.
    """
