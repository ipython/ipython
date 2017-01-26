"""
Shim to maintain backwards compatibility with old IPython.config imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

from IPython.utils.shimmodule import ShimModule, ShimWarning

warn("The `IPython.config` module has been deprecated. "
     "You should import from traitlets.config instead.", ShimWarning)


# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.config'] = ShimModule(src='IPython.config', mirror='traitlets.config')
