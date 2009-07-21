#!/usr/bin/env python
# encoding: utf-8
"""
Extra capabilities for IPython
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

from IPython.lib.inputhook import (
    enable_wx, disable_wx,
    enable_gtk, disable_gtk,
    enable_qt4, disable_qt4,
    enable_tk, disable_tk
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------