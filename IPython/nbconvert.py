"""
Shim to maintain backwards compatibility with old IPython.nbconvert imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.nbconvert` package has been deprecated. "
     "You should import from ipython_nbconvert instead.")

from IPython.utils.shimmodule import ShimModule

# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.nbconvert'] = ShimModule(
    src='IPython.nbconvert', mirror='jupyter_nbconvert')
