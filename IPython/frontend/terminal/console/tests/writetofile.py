#-----------------------------------------------------------------------------
# Copyright (C) 2012 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

"""
Copy data from input file to output file for testing.
"""

import sys
from IPython.utils.py3compat import PY3
(inpath, outpath) = sys.argv[1:]

if inpath == '-':
    if PY3:
        infile = sys.stdin.buffer
    else:
        infile = sys.stdin
else:
    infile = open(inpath, 'rb')

open(outpath, 'w+b').write(infile.read())
