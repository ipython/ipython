#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script. 
Under Windows, the command sdist is not supported, since IPython 
requires utilities, which are not available under Windows."""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Stdlib imports
import os
import sys
import py2exe
from glob import glob
from setupext import install_data_ext

from distutils.core import setup

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly

# Release.py contains version, authors, license, url, keywords, etc.
execfile(pjoin('IPython','Release.py'))

# A little utility we'll need below, since glob() does NOT allow you to do
# exclusion on multiple endings!
def file_doesnt_endwith(test,endings):
    """Return true if test is a file and its name does NOT end with any
    of the strings listed in endings."""
    if not isfile(test):
        return False
    for e in endings:
        if test.endswith(e):
            return False
    return True


# Call the setup() routine which does most of the work
setup(name             = name,
      version          = version,
      packages         = ['IPython', 'IPython.Extensions', 'IPython.external'],
      console = ['ipython.py'],
      scripts          = ['ipython.py'],
      # extra params needed for eggs
      )
