#!/usr/bin/env python
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

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------
from __future__ import print_function

import sys

# This check is also made in IPython/__init__, don't forget to update both when
# changing Python version requirements.
v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,3)):
    error = "ERROR: IPython requires Python version 2.7 or 3.3 or above."
    print(error, file=sys.stderr)
    sys.exit(1)

PY3 = (sys.version_info[0] >= 3)

# At least we're on the python version we need, move on.

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Stdlib imports
import os
import shutil

from glob import glob

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
from distutils.command.upload import upload

class UploadWindowsInstallers(upload):

    description = "Upload Windows installers to PyPI (only used from tools/release_windows.py)"
    user_options = upload.user_options + [
        ('files=', 'f', 'exe file (or glob) to upload')
    ]
    def initialize_options(self):
        upload.initialize_options(self)
        meta = self.distribution.metadata
        base = '{name}-{version}'.format(
            name=meta.get_name(),
            version=meta.get_version()
        )
        self.files = os.path.join('dist', '%s.*.exe' % base)

    def run(self):
        for dist_file in glob(self.files):
            self.upload_file('bdist_wininst', 'any', dist_file)

setup_args['cmdclass'] = {
    'build_py': \
            check_package_data_first(git_prebuild('IPython')),
    'sdist' : git_prebuild('IPython', sdist),
    'upload_wininst' : UploadWindowsInstallers,
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
needs_setuptools = set(('develop', 'release', 'bdist_egg', 'bdist_rpm',
           'bdist', 'bdist_dumb', 'bdist_wininst', 'bdist_wheel',
           'egg_info', 'easy_install', 'upload', 'install_egg_info',
            ))

if len(needs_setuptools.intersection(sys.argv)) > 0:
    import setuptools

# This dict is used for passing extra arguments that are setuptools
# specific to setup
setuptools_extra_args = {}

# setuptools requirements

extras_require = dict(
    parallel = ['ipyparallel'],
    qtconsole = ['qtconsole'],
    doc = ['Sphinx>=1.1', 'numpydoc'],
    test = ['nose>=0.10.1', 'requests', 'testpath'],
    terminal = [],
    kernel = ['ipykernel'],
    nbformat = ['nbformat'],
    notebook = ['notebook'],
    nbconvert = ['nbconvert'],
)
install_requires = [
    'decorator',
    'pickleshare',
    'simplegeneric>0.8',
    'traitlets',
]

# Platform-specific dependencies:
# This is the correct way to specify these,
# but requires pip >= 6. pip < 6 ignores these.
extras_require.update({
    ':sys_platform != "win32"': ['pexpect'],
    ':sys_platform == "darwin"': ['appnope', 'gnureadline'],
    'terminal:sys_platform == "win32"': ['pyreadline>=2'],
    'test:python_version == "2.7"': ['mock'],
})
# FIXME: re-specify above platform dependencies for pip < 6
# These would result in non-portable bdists.
if not any(arg.startswith('bdist') for arg in sys.argv):
    if sys.version_info < (3, 3):
        extras_require['test'].append('mock')

    if sys.platform == 'darwin':
        install_requires.extend(['appnope', 'gnureadline'])

    if sys.platform.startswith('win'):
        extras_require['terminal'].append('pyreadline>=2.0')
    else:
        install_requires.append('pexpect')

everything = set()
for deps in extras_require.values():
    everything.update(deps)
extras_require['all'] = everything

if 'setuptools' in sys.modules:
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
    requires = setup_args['install_requires'] = install_requires

    # Script to be run by the windows binary installer after the default setup
    # routine, to add shortcuts and similar windows-only things.  Windows
    # post-install scripts MUST reside in the scripts/ dir, otherwise distutils
    # doesn't find them.
    if 'bdist_wininst' in sys.argv:
        if len(sys.argv) > 2 and \
               ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
            print("ERROR: bdist_wininst must be run alone. Exiting.", file=sys.stderr)
            sys.exit(1)
        setup_args['data_files'].append(
            ['Scripts', ('scripts/ipython.ico', 'scripts/ipython_nb.ico')])
        setup_args['scripts'] = [pjoin('scripts','ipython_win_post_install.py')]
        setup_args['options'] = {"bdist_wininst":
                                 {"install_script":
                                  "ipython_win_post_install.py"}}

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
