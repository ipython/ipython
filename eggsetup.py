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

import sys, os
from glob import glob
from setupext import install_data_ext

isfile = os.path.isfile

if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from setuptools import setup


execfile(os.path.join('IPython','Release.py'))

cfgfiles    = filter(isfile, glob('IPython/UserConfig/*'))


# Call the setup() routine which does most of the work
setup(name             = name,
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
      packages         = ['IPython', 'IPython.Extensions'],
      cmdclass         = {'install_data': install_data_ext},
      data_files       = [
                          ('lib', 'IPython/UserConfig', cfgfiles)],
        # egg options
        entry_points = {
            'console_scripts': [
                'ipython = IPython.ipapi:launch_new_instance',
                'pycolor = IPython.PyColorize:main'
            ],
        }                          
      )
