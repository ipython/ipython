"""Implementation of all the magic functions built into IPython.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import annotations

import typing as t

from ..magic import Magics, magics_class
from ._table import (
    BUILTIN_LAZY_MAGICS,
    MAGICS_CLASSES,
    configured_script_magics,
    default_script_magics,
)

# The submodules are *not* imported here: they are loaded the first time one of
# their magics is used.  The names below stay importable from this package
# through the module `__getattr__` below.
if t.TYPE_CHECKING:
    from .auto import AutoMagics
    from .basic import AsyncMagics, BasicMagics
    from .code import CodeMagics, MacroToEdit
    from .config import ConfigMagics
    from .display import DisplayMagics
    from .execution import ExecutionMagics
    from .extension import ExtensionMagics
    from .history import HistoryMagics
    from .logging import LoggingMagics
    from .namespace import NamespaceMagics
    from .osm import OSMagics
    from .packaging import PackagingMagics
    from .pylab import PylabMagics
    from .script import ScriptMagics

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@magics_class
class UserMagics(Magics):
    """Placeholder for user-defined magics to be added at runtime.

    All magics are eventually merged into a single namespace at runtime, but we
    use this class to isolate the magics defined dynamically by the user into
    their own class.
    """


def __getattr__(name: str) -> t.Any:
    """Import the magics classes on first access (:pep:`562`)."""
    module_name = MAGICS_CLASSES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    obj = globals()[name] = getattr(import_module(module_name), name)
    return obj


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(MAGICS_CLASSES))
