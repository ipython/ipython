#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

import os
import sys

# Add my local path to sys.path
home = os.environ['HOME']
sys.path.insert(0,'%s/usr/local/lib/python%s/site-packages' %
                (home,sys.version[:3]))

# now, import setuptools and call the actual setup
import setuptools
print sys.argv
#sys.argv=['','bdist_egg']
execfile('setup.py')

# clean up the junk left around by setuptools
if "develop" not in sys.argv:
    os.system('rm -rf ipython.egg-info build')
