#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IPython -- An enhanced Interactive Python

The actual ipython script to be installed with 'python setup.py install' is
in './scripts' directory. This file is here (ipython source root directory)
to facilitate non-root 'zero-installation' (just copy the source tree
somewhere and run ipython.py) and development. """

if __name__ != "__main__":
    raise RuntimeError('You are trying to import the ipython.py executable. '
            'Did you mean to call "import IPython" (case-sensitive) instead?')

# Ensure that the imported IPython is the local one, not a system-wide one
import os, sys
this_dir = os.path.dirname(sys.argv[0])
sys.path.insert(0, this_dir)

# Now proceed with execution
execfile(os.path.join(
    this_dir, 'IPython', 'scripts', 'ipython'
))

