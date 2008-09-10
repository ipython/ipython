#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

import sys

# now, import setuptools and call the actual setup
import setuptools
# print sys.argv
#sys.argv=['','bdist_egg']
execfile('setup.py')

# clean up the junk left around by setuptools
if "develop" not in sys.argv:
    os.system('rm -rf ipython.egg-info build')
