#!/usr/bin/env python
# encoding: utf-8
"""
A backwards compatibility layer for IPython.Shell.

Previously, IPython had an IPython.Shell module.  IPython.Shell has been moved
to IPython.core.shell and is being refactored.  This new module is provided
for backwards compatability.  We strongly encourage everyone to start using
the new code in IPython.core.shell.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from warnings import warn

msg = """
This module (IPython.Shell) is deprecated.  The classes that were in this
module have been replaced by:

IPShell->IPython.core.iplib.InteractiveShell
IPShellEmbed->IPython.core.embed.InteractiveShellEmbed

Please migrate your code to use these classes instead.
"""

warn(msg, category=DeprecationWarning, stacklevel=1)

from IPython.core.iplib import InteractiveShell as IPShell
from IPython.core.embed import InteractiveShellEmbed as IPShellEmbed

def start(user_ns=None, embedded=False):
    """Return an instance of :class:`InteractiveShell`."""
    if embedded:
        return IPShellEmbed(user_ns=user_ns)
    else:
        return IPShell(user_ns=user_ns)

