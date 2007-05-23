#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for exe distribution of IPython (does not require python).

- Requires py2exe

- install pyreadline in ipython root directory by running:
  
svn co http://ipython.scipy.org/svn/ipython/pyreadline/trunk pyreadline

- Create the distribution in 'dist' by running "python exesetup.py py2exe"

- Run ipython.exe to go.

"""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Stdlib imports
import os
import sys

from glob import glob


# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join

from distutils.core import setup
import py2exe

# update the manuals when building a source dist
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


if 'setuptools' in sys.modules:
    # setuptools config for egg building
    egg_extra_kwds = {
        'entry_points': {
            'console_scripts': [
            'ipython = IPython.ipapi:launch_new_instance',
            'pycolor = IPython.PyColorize:main'
            ]}
        }
    scriptfiles = []
    # eggs will lack docs, examples XXX not anymore
    #datafiles = [('lib', 'IPython/UserConfig', cfgfiles)]
else:
    egg_extra_kwds = {}


# Call the setup() routine which does most of the work
setup(name             = name,
    options   = {
        'py2exe': {
                      'packages' : ['IPython', 'IPython.Extensions', 'IPython.external','pyreadline'],
                     }
    },
    version          = version,
    description      = description,
    long_description = long_description,
    author           = authors['Fernando'][0],
    author_email     = authors['Fernando'][1],
    url              = url,
    download_url     = download_url,
    license          = license,
    platforms        = platforms,
    keywords         = keywords,
    packages         = ['IPython', 'IPython.Extensions', 'IPython.external'],
    console          = ['ipython.py'],
    
    # extra params needed for eggs
    **egg_extra_kwds                        
    )
