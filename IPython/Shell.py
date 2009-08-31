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
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from warnings import warn

msg = """
This module (IPython.Shell) has been moved to a new location
(IPython.core.shell) and is being refactored.  Please update your code
to use the new IPython.core.shell module"""

warn(msg, category=DeprecationWarning, stacklevel=1)

from IPython.core.shell import start, IPShell, IPShellEmbed

