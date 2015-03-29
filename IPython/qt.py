"""
Shim to maintain backwards compatibility with old IPython.qt imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.qt` package has been deprecated. "
     "You should import from jupyter_qtconsole instead.")

from IPython.utils.shimmodule import ShimModule

# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.qt'] = ShimModule(src='IPython.qt', mirror='jupyter_qtconsole')
