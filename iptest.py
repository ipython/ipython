#!/usr/bin/env python
"""Test script for IPython.

The actual ipython test script to be installed with 'python setup.py install'
is in './scripts' directory. This file is here (ipython source root directory)
to facilitate non-root 'zero-installation testing' (just copy the source tree
somewhere and run ipython.py) and development.

You can run this script directly, type -h to see all options."""

# Ensure that the imported IPython is the local one, not a system-wide one
import os, sys
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, this_dir)

# Now proceed with execution
execfile(os.path.join(this_dir, 'IPython', 'scripts', 'iptest'))
