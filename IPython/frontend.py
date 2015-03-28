"""
Shim to maintain backwards compatibility with old frontend imports.

We have moved all contents of the old `frontend` subpackage into top-level
subpackages (`html`, `qt` and `terminal`), and flattened the notebook into
just `IPython.html`, formerly `IPython.frontend.html.notebook`.

This will let code that was making `from IPython.frontend...` calls continue
working, though a warning will be printed.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

# Stdlib
import sys
import types
from warnings import warn

warn("The top-level `frontend` package has been deprecated. "
     "All its subpackages have been moved to the top `IPython` level.")

from IPython.utils.shimmodule import ShimModule

# Unconditionally insert the shim into sys.modules so that further import calls
# trigger the custom attribute access above

sys.modules['IPython.frontend.html.notebook'] = ShimModule('notebook', mirror='IPython.html')
sys.modules['IPython.frontend'] = ShimModule('frontend', mirror='IPython')
