"""
Shim to maintain backwards compatibility with old IPython.terminal.console imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import sys
from warnings import warn

warn("The `IPython.terminal.console` package has been deprecated. "
     "You should import from jupyter_console instead.")

from IPython.utils.shimmodule import ShimModule

# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.terminal.console'] = ShimModule(
    src='IPython.terminal.console', mirror='jupyter_console')
