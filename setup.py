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
from itertools import chain

# **Python version check**
#
# This check is also made in IPython/__init__, don't forget to update both when
# changing Python version requirements.
if sys.version_info < (3, 8):
    pip_message = 'This may be due to an out of date pip. Make sure you have pip >= 9.0.1.'
    try:
        import pip
        pip_version = tuple([int(x) for x in pip.__version__.split('.')[:3]])
        if pip_version < (9, 0, 1) :
            pip_message = 'Your pip version is out of date, please install pip >= 9.0.1. '\
            'pip {} detected.'.format(pip.__version__)
        else:
            # pip is new enough - it must be something else
            pip_message = ''
    except Exception:
        pass


    error = """
IPython 8+ supports Python 3.8 and above, following NEP 29.
When using Python 2.7, please install IPython 5.x LTS Long Term Support version.
Python 3.3 and 3.4 were supported up to IPython 6.x.
Python 3.5 was supported with IPython 7.0 to 7.9.
Python 3.6 was supported with IPython up to 7.16.
Python 3.7 was still supported with the 7.x branch.

See IPython `README.rst` file for more information:

    https://github.com/ipython/ipython/blob/master/README.rst

Python {py} detected.
{pip}
""".format(py=sys.version_info, pip=pip_message )

    print(error, file=sys.stderr)
    sys.exit(1)

# At least we're on the python version we need, move on.

from setuptools import setup

# Our own imports
from setupbase import target_update

from setupbase import (
    setup_args,
    check_package_data_first,
    find_data_files,
    git_prebuild,
    install_symlinked,
    install_lib_symlink,
    install_scripts_for_symlink,
    unsymlink,
)

#-------------------------------------------------------------------------------
# Handle OS specific things
#-------------------------------------------------------------------------------

if os.name in ('nt','dos'):
    os_name = 'windows'
else:
    os_name = os.name

# Under Windows, 'sdist' has not been supported.  Now that the docs build with
# Sphinx it might work, but let's not turn it on until someone confirms that it
# actually works.
if os_name == 'windows' and 'sdist' in sys.argv:
    print('The sdist command is not available under Windows.  Exiting.')
    sys.exit(1)


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
    'symlink': install_symlinked,
    'install_lib_symlink': install_lib_symlink,
    'install_scripts_sym': install_scripts_for_symlink,
    'unsymlink': unsymlink,
}


#---------------------------------------------------------------------------
# Handle scripts, dependencies, and setuptools specific things
#---------------------------------------------------------------------------

# setuptools requirements

extras_require = dict(
    parallel=["ipyparallel"],
    qtconsole=["qtconsole"],
    doc=["Sphinx>=1.3"],
    test=[
        "pytest",
        "pytest-asyncio",
        "testpath",
        "pygments",
    ],
    test_extra=[
        "pytest",
        "testpath",
        "curio",
        "matplotlib!=3.2.0",
        "nbformat",
        "numpy>=1.19",
        "pandas",
        "pygments",
        "trio",
    ],
    terminal=[],
    kernel=["ipykernel"],
    nbformat=["nbformat"],
    notebook=["notebook", "ipywidgets"],
    nbconvert=["nbconvert"],
)

everything = set(chain.from_iterable(extras_require.values()))
extras_require['all'] = list(sorted(everything))

setup_args["extras_require"] = extras_require

#---------------------------------------------------------------------------
# Do the actual setup now
#---------------------------------------------------------------------------

if __name__ == "__main__":
    setup(**setup_args)
