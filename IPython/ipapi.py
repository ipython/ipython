#!/usr/bin/env python
# encoding: utf-8
"""
A backwards compatibility layer for IPython.ipapi.

Previously, IPython had an IPython.ipapi module.  IPython.ipapi has been moved
to IPython.core.ipapi and is being refactored.  This new module is provided
for backwards compatability.  We strongly encourage everyone to start using
the new code in IPython.core.ipapi.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from warnings import warn

msg = """
This module (IPython.ipapi) has been moved to a new location
(IPython.core.ipapi) and is being refactored.  Please update your code
to use the new IPython.core.ipapi module"""

warn(msg, category=DeprecationWarning, stacklevel=1)

from IPython.core.ipapi import *

