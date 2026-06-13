"""
Utilities for working with stack frames.
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

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def extract_module_locals(depth: int = 0) -> tuple[ModuleType, dict[str, Any]]:
    """Returns (module, locals) of the function `depth` frames away from the caller"""
    f = sys._getframe(depth + 1)
    global_ns = f.f_globals
    module = sys.modules[global_ns['__name__']]
    return (module, f.f_locals)
