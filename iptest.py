#!/usr/bin/env python
"""Test script for IPython.

The actual ipython test script to be installed with 'python setup.py install'
is in './scripts' directory, and will test IPython from an importable
location.

This file is here (ipython source root directory) to facilitate non-root
'zero-installation testing and development' (just copy the source tree
somewhere and run iptest.py).

You can run this script directly, type -h to see all options."""

# Ensure that the imported IPython packages come from *THIS* IPython, not some
# other one that may exist system-wide
import os, sys
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, this_dir)

# Now proceed with execution
execfile(os.path.join(this_dir, 'IPython', 'scripts', 'iptest'))
