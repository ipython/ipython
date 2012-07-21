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
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------
from __future__ import print_function

import sys

# This check is also made in IPython/__init__, don't forget to update both when
# changing Python version requirements.
#~ if sys.version[0:3] < '2.6':
    #~ error = """\
#~ ERROR: 'IPython requires Python Version 2.6 or above.'
#~ Exiting."""
    #~ print >> sys.stderr, error
    #~ sys.exit(1)

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

# On Python 3, we need distribute (new setuptools) to do the 2to3 conversion
if PY3:
    import setuptools

# Our own imports
from setupbase import target_update

from setupbase import (
    setup_args,
    find_packages,
    find_package_data,
    find_scripts,
    find_data_files,
    check_for_dependencies,
    record_commit_info,
)
from setupext import setupext

isfile = os.path.isfile
pjoin = os.path.join

#-----------------------------------------------------------------------------
# Function definitions
#-----------------------------------------------------------------------------

def cleanup():
    """Clean up the junk left around by the build process"""
    if "develop" not in sys.argv:
        try:
            shutil.rmtree('ipython.egg-info')
        except:
            try:
                os.unlink('ipython.egg-info')
            except:
                pass

#-------------------------------------------------------------------------------
# Handle OS specific things
#-------------------------------------------------------------------------------

if os.name == 'posix':
    os_name = 'posix'
elif os.name in ['nt','dos']:
    os_name = 'windows'
else:
    print('Unsupported operating system:',os.name)
    sys.exit(1)

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
    import textwrap

    # List of things to be updated. Each entry is a triplet of args for
    # target_update()
    to_update = [
                  # FIXME - Disabled for now: we need to redo an automatic way
                  # of generating the magic info inside the rst.
                  #('docs/magic.tex',
                  #['IPython/Magic.py'],
                  #"cd doc && ./update_magic.sh" ),

                 ('docs/man/ipcluster.1.gz',
                  ['docs/man/ipcluster.1'],
                  'cd docs/man && gzip -9c ipcluster.1 > ipcluster.1.gz'),

                 ('docs/man/ipcontroller.1.gz',
                  ['docs/man/ipcontroller.1'],
                  'cd docs/man && gzip -9c ipcontroller.1 > ipcontroller.1.gz'),

                 ('docs/man/ipengine.1.gz',
                  ['docs/man/ipengine.1'],
                  'cd docs/man && gzip -9c ipengine.1 > ipengine.1.gz'),

                 ('docs/man/iplogger.1.gz',
                  ['docs/man/iplogger.1'],
                  'cd docs/man && gzip -9c iplogger.1 > iplogger.1.gz'),

                 ('docs/man/ipython.1.gz',
                  ['docs/man/ipython.1'],
                  'cd docs/man && gzip -9c ipython.1 > ipython.1.gz'),

                 ('docs/man/irunner.1.gz',
                  ['docs/man/irunner.1'],
                  'cd docs/man && gzip -9c irunner.1 > irunner.1.gz'),

                 ('docs/man/pycolor.1.gz',
                  ['docs/man/pycolor.1'],
                  'cd docs/man && gzip -9c pycolor.1 > pycolor.1.gz'),
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
    'build_py': record_commit_info('IPython'),
    'sdist' : record_commit_info('IPython', sdist),
    'upload_wininst' : UploadWindowsInstallers,
}

#---------------------------------------------------------------------------
# Handle scripts, dependencies, and setuptools specific things
#---------------------------------------------------------------------------

# For some commands, use setuptools.  Note that we do NOT list install here!
# If you want a setuptools-enhanced install, just run 'setupegg.py install'
needs_setuptools = set(('develop', 'release', 'bdist_egg', 'bdist_rpm',
           'bdist', 'bdist_dumb', 'bdist_wininst', 'install_egg_info',
           'egg_info', 'easy_install', 'upload',
            ))
if sys.platform == 'win32':
    # Depend on setuptools for install on *Windows only*
    # If we get script-installation working without setuptools,
    # then we can back off, but until then use it.
    # See Issue #369 on GitHub for more
    needs_setuptools.add('install')

if len(needs_setuptools.intersection(sys.argv)) > 0:
    import setuptools

# This dict is used for passing extra arguments that are setuptools
# specific to setup
setuptools_extra_args = {}

if 'setuptools' in sys.modules:
    setuptools_extra_args['zip_safe'] = False
    setuptools_extra_args['entry_points'] = find_scripts(True)
    setup_args['extras_require'] = dict(
        parallel = 'pyzmq>=2.1.4',
        zmq = 'pyzmq>=2.1.4',
        doc = 'Sphinx>=0.3',
        test = 'nose>=0.10.1',
        notebook = 'tornado>=2.0'
    )
    requires = setup_args.setdefault('install_requires', [])
    setupext.display_status = False
    if not setupext.check_for_readline():
        if sys.platform == 'darwin':
            requires.append('readline')
        elif sys.platform.startswith('win'):
            # Pyreadline 64 bit windows issue solved in versions >=1.7.1
            # Also solves issues with some older versions of pyreadline that
            # satisfy the unconstrained depdendency.
            requires.append('pyreadline>=1.7.1')
        else:
            pass
            # do we want to install readline here?

    # Script to be run by the windows binary installer after the default setup
    # routine, to add shortcuts and similar windows-only things.  Windows
    # post-install scripts MUST reside in the scripts/ dir, otherwise distutils
    # doesn't find them.
    if 'bdist_wininst' in sys.argv:
        if len(sys.argv) > 2 and \
               ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
            print >> sys.stderr, "ERROR: bdist_wininst must be run alone. Exiting."
            sys.exit(1)
        setup_args['scripts'] = [pjoin('scripts','ipython_win_post_install.py')]
        setup_args['options'] = {"bdist_wininst":
                                 {"install_script":
                                  "ipython_win_post_install.py"}}
    
    if PY3:
        setuptools_extra_args['use_2to3'] = True
        from setuptools.command.build_py import build_py
        setup_args['cmdclass'] = {'build_py': record_commit_info('IPython', build_cmd=build_py)}
        setuptools_extra_args['entry_points'] = find_scripts(True, suffix='3')
        setuptools._dont_write_bytecode = True
else:
    # If we are running without setuptools, call this function which will
    # check for dependencies an inform the user what is needed.  This is
    # just to make life easy for users.
    check_for_dependencies()
    setup_args['scripts'] = find_scripts(False)

#---------------------------------------------------------------------------
# Do the actual setup now
#---------------------------------------------------------------------------

setup_args.update(setuptools_extra_args)

def main():
    setup(**setup_args)
    cleanup()

if __name__ == '__main__':
    main()
