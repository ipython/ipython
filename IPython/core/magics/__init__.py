"""Implementation of all the magic functions built into IPython.
"""

# -----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from ..magic import Magics as Magics, magics_class as magics_class
from .auto import AutoMagics as AutoMagics
from .basic import BasicMagics as BasicMagics, AsyncMagics as AsyncMagics
from .code import CodeMagics as CodeMagics, MacroToEdit as MacroToEdit
from .config import ConfigMagics as ConfigMagics
from .display import DisplayMagics as DisplayMagics
from .execution import ExecutionMagics as ExecutionMagics
from .extension import ExtensionMagics as ExtensionMagics
from .history import HistoryMagics as HistoryMagics
from .logging import LoggingMagics as LoggingMagics
from .namespace import NamespaceMagics as NamespaceMagics
from .osm import OSMagics as OSMagics
from .packaging import PackagingMagics as PackagingMagics
from .pylab import PylabMagics as PylabMagics
from .script import ScriptMagics as ScriptMagics


# -----------------------------------------------------------------------------
# Magic implementation classes
# -----------------------------------------------------------------------------


@magics_class
class UserMagics(Magics):
    """Placeholder for user-defined magics to be added at runtime.

    All magics are eventually merged into a single namespace at runtime, but we
    use this class to isolate the magics defined dynamically by the user into
    their own class.
    """
