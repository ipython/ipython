"""[DEPRECATED] Utilities for connecting to kernels

Moved to IPython.kernel.connect
"""

import warnings
warnings.warn("IPython.lib.kernel moved to IPython.kernel.connect in IPython 1.0",
    DeprecationWarning
)

from IPython.kernel.connect import *

