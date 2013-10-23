"""Load our patched versions of tokenize.
"""

import sys

if sys.version_info[0] >= 3:
    from ._tokenize_py3 import *
else:
    from ._tokenize_py2 import *
