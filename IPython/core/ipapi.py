#!/usr/bin/env python
# encoding: utf-8
"""
Oh my @#*%, where did ipapi go?

Originally, this module was designed to be a public api for IPython.  It is
now deprecated and replaced by :class:`IPython.core.Interactive` shell.
Almost all of the methods that were here are now there, but possibly renamed.

During our transition, we will keep this simple module with its :func:`get`
function.  It too will eventually go away when the new component querying
interface is fully used.

Authors:

* Brian Granger
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

from IPython.core.error import TryNext, UsageError
from IPython.core.component import Component

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def get():
    """Get the most recently created InteractiveShell instance."""
    insts = Component.get_instances(name='__IP')
    most_recent = insts[0]
    for inst in insts[1:]:
        if inst.created > most_recent.created:
            most_recent = inst
    return most_recent

def launch_new_instance():
    """Create a run a full blown IPython instance"""
    from IPython.core.ipapp import IPythonApp
    app = IPythonApp()
    app.start()








