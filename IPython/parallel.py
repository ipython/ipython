"""
Shim to maintain backwards compatibility with old IPython.parallel imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.parallel` package has been deprecated. "
     "You should import from ipython_parallel instead.")

from IPython.utils.shimmodule import ShimModule

# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.parallel'] = ShimModule(
    src='IPython.parallel', mirror='ipython_parallel')

