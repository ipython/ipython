"""[DEPRECATED] Utilities for connecting to kernels

Moved to IPython.utils.kernel, where it always belonged.
"""

import warnings
warnings.warn("IPython.lib.kernel moved to IPython.utils.kernel in IPython 0.14",
    DeprecationWarning
)

from IPython.utils.kernel import *

