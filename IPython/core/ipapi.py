#!/usr/bin/env python
# encoding: utf-8
"""
This module is *completely* deprecated and should no longer be used for
any purpose.  Currently, we have a few parts of the core that have
not been componentized and thus, still rely on this module.  When everything
has been made into a component, this module will be sent to deathrow.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


def get():
    """Get the most recently created InteractiveShell instance."""
    from IPython.core.iplib import InteractiveShell
    insts = InteractiveShell.get_instances()
    if len(insts)==0:
        return None
    most_recent = insts[0]
    for inst in insts[1:]:
        if inst.created > most_recent.created:
            most_recent = inst
    return most_recent
