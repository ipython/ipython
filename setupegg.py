#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

import os
import shutil
import sys

# now, import setuptools and call the actual setup
import setuptools
execfile('setup.py')

# clean up the junk left around by setuptools
if "develop" not in sys.argv:
    try:
        shutil.rmtree('ipython.egg-info')
    except:
        try:
            os.unlink('ipython.egg-info')
        except:
            pass
