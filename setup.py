#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script. 
Under Windows, the command sdist is not supported, since IPython 
requires utilities which are not available under Windows."""

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Stdlib imports
import os
import sys

from glob import glob

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

# Local imports
from IPython.genutils import target_update

from setupbase import (
    setup_args, 
    find_packages, 
    find_package_data, 
    find_scripts,
    find_data_files,
    check_for_dependencies
)

isfile = os.path.isfile

#-------------------------------------------------------------------------------
# Handle OS specific things
#-------------------------------------------------------------------------------

if os.name == 'posix':
    os_name = 'posix'
elif os.name in ['nt','dos']:
    os_name = 'windows'
else:
    print 'Unsupported operating system:',os.name
    sys.exit(1)

# Under Windows, 'sdist' has not been supported.  Now that the docs build with
# Sphinx it might work, but let's not turn it on until someone confirms that it
# actually works.
if os_name == 'windows' and 'sdist' in sys.argv:
    print 'The sdist command is not available under Windows.  Exiting.'
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
                 
                 ('docs/man/ipython.1.gz',
                  ['docs/man/ipython.1'],
                  "cd docs/man && gzip -9c ipython.1 > ipython.1.gz"),

                 ('docs/man/pycolor.1.gz',
                  ['docs/man/pycolor.1'],
                  "cd docs/man && gzip -9c pycolor.1 > pycolor.1.gz"),
                 ]

    # Only build the docs if sphinx is present
    try:
        import sphinx
    except ImportError:
        pass
    else:
        # The Makefile calls the do_sphinx scripts to build html and pdf, so
        # just one target is enough to cover all manual generation

        # First, compute all the dependencies that can force us to rebuild the
        # docs.  Start with the main release file that contains metadata
        docdeps = ['IPython/Release.py']
        # Inculde all the reST sources
        pjoin = os.path.join
        for dirpath,dirnames,filenames in os.walk('docs/source'):
            if dirpath in ['_static','_templates']:
                continue
            docdeps += [ pjoin(dirpath,f) for f in filenames
                         if f.endswith('.txt') ]
        # and the examples
        for dirpath,dirnames,filenames in os.walk('docs/example'):
            docdeps += [ pjoin(dirpath,f) for f in filenames
                         if not f.endswith('~') ]
        # then, make them all dependencies for the main PDF (the html will get
        # auto-generated as well).
        to_update.append(
            ('docs/dist/ipython.pdf',
             docdeps,
             "cd docs && make dist")
            )
        
    [ target_update(*t) for t in to_update ]

    
#---------------------------------------------------------------------------
# Find all the packages, package data, scripts and data_files
#---------------------------------------------------------------------------

packages = find_packages()
package_data = find_package_data()
scripts = find_scripts()
data_files = find_data_files()

#---------------------------------------------------------------------------
# Handle dependencies and setuptools specific things
#---------------------------------------------------------------------------

# This dict is used for passing extra arguments that are setuptools 
# specific to setup
setuptools_extra_args = {}

if 'setuptools' in sys.modules:
    setuptools_extra_args['zip_safe'] = False
    setuptools_extra_args['entry_points'] = {
        'console_scripts': [
            'ipython = IPython.ipapi:launch_new_instance',
            'pycolor = IPython.PyColorize:main',
            'ipcontroller = IPython.kernel.scripts.ipcontroller:main',
            'ipengine = IPython.kernel.scripts.ipengine:main',
            'ipcluster = IPython.kernel.scripts.ipcluster:main',
            'ipythonx = IPython.frontend.wx.ipythonx:main',
            'iptest = IPython.testing.iptest:main',
        ]
    }
    setup_args['extras_require'] = dict(
        kernel = [
            'zope.interface>=3.4.1',
            'Twisted>=8.0.1',
            'foolscap>=0.2.6'
        ],
        doc='Sphinx>=0.3',
        test='nose>=0.10.1',
        security='pyOpenSSL>=0.6'
    )
    # Allow setuptools to handle the scripts
    scripts = []
else:
    # package_data of setuptools was introduced to distutils in 2.4
    cfgfiles = filter(isfile, glob('IPython/UserConfig/*'))
    if sys.version_info < (2,4):
        data_files.append(('lib', 'IPython/UserConfig', cfgfiles))
    # If we are running without setuptools, call this function which will
    # check for dependencies an inform the user what is needed.  This is
    # just to make life easy for users.
    check_for_dependencies()


#---------------------------------------------------------------------------
# Do the actual setup now
#---------------------------------------------------------------------------

setup_args['packages'] = packages
setup_args['package_data'] = package_data
setup_args['scripts'] = scripts
setup_args['data_files'] = data_files
setup_args.update(setuptools_extra_args)

if __name__ == '__main__':
    setup(**setup_args)
