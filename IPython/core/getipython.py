"""Simple function to call to get the current InteractiveShell instance"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Classes and functions
# -----------------------------------------------------------------------------
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell


def get_ipython() -> "InteractiveShell | None":
    """Get the global InteractiveShell instance.

    Returns None if no InteractiveShell instance is registered.
    """
    from IPython.core.interactiveshell import InteractiveShell

    if InteractiveShell.initialized():
        return InteractiveShell.instance()
