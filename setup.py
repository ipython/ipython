# -*- coding: utf-8 -*-
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script.
Under Windows, the command sdist is not supported, since IPython
requires utilities which are not available under Windows."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.rst, distributed with this software.
#-----------------------------------------------------------------------------

import os
import sys

# At least we're on the python version we need, move on.

from setuptools import setup

# Our own imports

from setupbase import target_update

from setupbase import (
    setup_args,
    check_package_data_first,
    find_data_files,
    git_prebuild,
)

#-------------------------------------------------------------------------------
# Things related to the IPython documentation
#-------------------------------------------------------------------------------

# update the manuals when building a source dist
if len(sys.argv) >= 2 and sys.argv[1] in ('sdist','bdist_rpm'):

    # List of things to be updated. Each entry is a triplet of args for
    # target_update()
    to_update = [
        (
            "docs/man/ipython.1.gz",
            ["docs/man/ipython.1"],
            "cd docs/man && python -m gzip --best ipython.1",
        ),
    ]


    [ target_update(*t) for t in to_update ]

#---------------------------------------------------------------------------
# Find all the packages, package data, and data_files
#---------------------------------------------------------------------------

data_files = find_data_files()

setup_args['data_files'] = data_files

#---------------------------------------------------------------------------
# custom distutils commands
#---------------------------------------------------------------------------
# imports here, so they are after setuptools import if there was one
from setuptools.command.sdist import sdist

setup_args['cmdclass'] = {
    'build_py': \
            check_package_data_first(git_prebuild('IPython')),
    'sdist' : git_prebuild('IPython', sdist),
}

#---------------------------------------------------------------------------
# Do the actual setup now
#---------------------------------------------------------------------------

if __name__ == "__main__":
    setup(**setup_args)
