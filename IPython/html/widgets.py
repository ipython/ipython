"""
Shim to maintain backwards compatibility with old IPython.html.widgets imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.html.widgets` package has been deprecated. "
     "You should import from `ipython_widgets` instead.")

from IPython.utils.shimmodule import ShimModule

sys.modules['IPython.html.widgets'] = ShimModule(
    src='IPython.html.widgets', mirror='ipython_widgets')
