#!/usr/bin/env python3
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

from __future__ import print_function

import os
import sys

# **Python version check**
#
# This check is also made in IPython/__init__, don't forget to update both when
# changing Python version requirements.
if sys.version_info < (3, 5):
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
IPython 7.0+ supports Python 3.5 and above.
When using Python 2.7, please install IPython 5.x LTS Long Term Support version.
Python 3.3 and 3.4 were supported up to IPython 6.x.

See IPython `README.rst` file for more information:

    https://github.com/ipython/ipython/blob/master/README.rst

Python {py} detected.
{pip}
""".format(py=sys.version_info, pip=pip_message )

    print(error, file=sys.stderr)
    sys.exit(1)

# At least we're on the python version we need, move on.

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

# Our own imports
from setupbase import target_update

from setupbase import (
    setup_args,
    find_packages,
    find_package_data,
    check_package_data_first,
    find_entry_points,
    build_scripts_entrypt,
    find_data_files,
    git_prebuild,
    install_symlinked,
    install_lib_symlink,
    install_scripts_for_symlink,
    unsymlink,
)

isfile = os.path.isfile
pjoin = os.path.join

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
                 ('docs/man/ipython.1.gz',
                  ['docs/man/ipython.1'],
                  'cd docs/man && gzip -9c ipython.1 > ipython.1.gz'),
                 ]


    [ target_update(*t) for t in to_update ]

#---------------------------------------------------------------------------
# Find all the packages, package data, and data_files
#---------------------------------------------------------------------------

packages = find_packages()
package_data = find_package_data()

data_files = find_data_files()

setup_args['packages'] = packages
setup_args['package_data'] = package_data
setup_args['data_files'] = data_files

#---------------------------------------------------------------------------
# custom distutils commands
#---------------------------------------------------------------------------
# imports here, so they are after setuptools import if there was one
from distutils.command.sdist import sdist

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

# For some commands, use setuptools.  Note that we do NOT list install here!
# If you want a setuptools-enhanced install, just run 'setupegg.py install'
needs_setuptools = {'develop', 'release', 'bdist_egg', 'bdist_rpm',
           'bdist', 'bdist_dumb', 'bdist_wininst', 'bdist_wheel',
           'egg_info', 'easy_install', 'upload', 'install_egg_info',
          }

if len(needs_setuptools.intersection(sys.argv)) > 0:
    import setuptools

# This dict is used for passing extra arguments that are setuptools
# specific to setup
setuptools_extra_args = {}

# setuptools requirements

extras_require = dict(
    parallel = ['ipyparallel'],
    qtconsole = ['qtconsole'],
    doc = ['Sphinx>=1.3'],
    test = ['nose>=0.10.1', 'requests', 'testpath', 'pygments', 'nbformat', 'ipykernel', 'numpy'],
    terminal = [],
    kernel = ['ipykernel'],
    nbformat = ['nbformat'],
    notebook = ['notebook', 'ipywidgets'],
    nbconvert = ['nbconvert'],
)

install_requires = [
    'setuptools>=18.5',
    'jedi>=0.10',
    'decorator',
    'pickleshare',
    'traitlets>=4.2',
    'prompt_toolkit>=2.0.0,<2.1.0',
    'pygments',
    'backcall',
]

# Platform-specific dependencies:
# This is the correct way to specify these,
# but requires pip >= 6. pip < 6 ignores these.

extras_require.update({
    ':python_version == "3.4"': ['typing'],
    ':sys_platform != "win32"': ['pexpect'],
    ':sys_platform == "darwin"': ['appnope'],
    ':sys_platform == "win32"': ['colorama'],
    ':sys_platform == "win32" and python_version < "3.6"': ['win_unicode_console>=0.5'],
})
# FIXME: re-specify above platform dependencies for pip < 6
# These would result in non-portable bdists.
if not any(arg.startswith('bdist') for arg in sys.argv):
    if sys.platform == 'darwin':
        install_requires.extend(['appnope'])

    if not sys.platform.startswith('win'):
        install_requires.append('pexpect')

    # workaround pypa/setuptools#147, where setuptools misspells
    # platform_python_implementation as python_implementation
    if 'setuptools' in sys.modules:
        for key in list(extras_require):
            if 'platform_python_implementation' in key:
                new_key = key.replace('platform_python_implementation', 'python_implementation')
                extras_require[new_key] = extras_require.pop(key)

everything = set()
for key, deps in extras_require.items():
    if ':' not in key:
        everything.update(deps)
extras_require['all'] = everything

if 'setuptools' in sys.modules:
    setuptools_extra_args['python_requires'] = '>=3.5'
    setuptools_extra_args['zip_safe'] = False
    setuptools_extra_args['entry_points'] = {
        'console_scripts': find_entry_points(),
        'pygments.lexers': [
            'ipythonconsole = IPython.lib.lexers:IPythonConsoleLexer',
            'ipython = IPython.lib.lexers:IPythonLexer',
            'ipython3 = IPython.lib.lexers:IPython3Lexer',
        ],
    }
    setup_args['extras_require'] = extras_require
    setup_args['install_requires'] = install_requires

else:
    # scripts has to be a non-empty list, or install_scripts isn't called
    setup_args['scripts'] = [e.split('=')[0].strip() for e in find_entry_points()]

    setup_args['cmdclass']['build_scripts'] = build_scripts_entrypt

#---------------------------------------------------------------------------
# Do the actual setup now
#---------------------------------------------------------------------------

setup_args.update(setuptools_extra_args)



def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
