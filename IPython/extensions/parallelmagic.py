# encoding: utf-8
"""
=============
parallelmagic
=============

Deprecated, parallel magics are no longer an extension.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from warnings import warn

def load_ipython_extension(ip):
    warn("Parallel Magics are no longer defined in an extension", DeprecationWarning)
