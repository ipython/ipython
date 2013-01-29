"""[DEPRECATED] Utilities for connecting to kernels

Moved to IPython.kernel.connect
"""

import warnings
warnings.warn("IPython.lib.kernel moved to IPython.kernel.connect in IPython 0.14",
    DeprecationWarning
)

from IPython.kernel.connect import *

