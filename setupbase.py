# encoding: utf-8

"""
This module defines the things that are used in setup.py for building IPython

This includes:

    * The basic arguments to setup
    * Functions for finding things like packages, package data, etc.
    * A function for checking dependencies.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os, sys

from glob import glob

from setupext import install_data_ext

#-------------------------------------------------------------------------------
# Useful globals and utility functions
#-------------------------------------------------------------------------------

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join

def oscmd(s):
    print ">", s
    os.system(s)

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

#---------------------------------------------------------------------------
# Basic project information
#---------------------------------------------------------------------------

# Release.py contains version, authors, license, url, keywords, etc.
execfile(pjoin('IPython','Release.py'))

# Create a dict with the basic information
# This dict is eventually passed to setup after additional keys are added.
setup_args = dict(
      name             = name,
      version          = version,
      description      = description,
      long_description = long_description,
      author           = author,
      author_email     = author_email,
      url              = url,
      download_url     = download_url,
      license          = license,
      platforms        = platforms,
      keywords         = keywords,
      cmdclass         = {'install_data': install_data_ext},
      )


#---------------------------------------------------------------------------
# Find packages
#---------------------------------------------------------------------------

def add_package(packages, pname, config=False, tests=False, scripts=False, others=None):
    """
    Add a package to the list of packages, including certain subpackages.
    """
    packages.append('.'.join(['IPython',pname]))
    if config:
        packages.append('.'.join(['IPython',pname,'config']))
    if tests:
        packages.append('.'.join(['IPython',pname,'tests']))
    if scripts:
        packages.append('.'.join(['IPython',pname,'scripts']))
    if others is not None:
        for o in others:
            packages.append('.'.join(['IPython',pname,o]))

def find_packages():
    """
    Find all of IPython's packages.
    """
    packages = ['IPython']
    add_package(packages, 'config', tests=True)
    add_package(packages , 'Extensions')
    add_package(packages, 'external')
    add_package(packages, 'gui')
    add_package(packages, 'gui.wx')
    add_package(packages, 'frontend')
    add_package(packages, 'frontend._process')
    add_package(packages, 'frontend.wx')
    add_package(packages, 'frontend.cocoa')
    add_package(packages, 'kernel', config=True, tests=True, scripts=True)
    add_package(packages, 'kernel.core', config=True, tests=True)
    add_package(packages, 'testing', tests=True)
    add_package(packages, 'tools', tests=True)
    add_package(packages, 'UserConfig')
    return packages

#---------------------------------------------------------------------------
# Find package data
#---------------------------------------------------------------------------

def find_package_data():
    """
    Find IPython's package_data.
    """
    # This is not enough for these things to appear in an sdist.
    # We need to muck with the MANIFEST to get this to work
    package_data = {
        'IPython.UserConfig' : ['*'],
        'IPython.tools.tests' : ['*.txt'],
        'IPython.testing' : ['*.txt']
    }
    return package_data


#---------------------------------------------------------------------------
# Find data files
#---------------------------------------------------------------------------

def find_data_files():
    """
    Find IPython's data_files.
    """
    
    # I can't find how to make distutils create a nested dir. structure, so
    # in the meantime do it manually. Butt ugly.
    # Note that http://www.redbrick.dcu.ie/~noel/distutils.html, ex. 2/3, contain
    # information on how to do this more cleanly once python 2.4 can be assumed.
    # Thanks to Noel for the tip.
    docdirbase  = 'share/doc/ipython'
    manpagebase = 'share/man/man1'

    # We only need to exclude from this things NOT already excluded in the
    # MANIFEST.in file.
    exclude     = ('.sh','.1.gz')
    # We need to figure out how we want to package all of our rst docs?
    # docfiles    = filter(lambda f:file_doesnt_endwith(f,exclude),glob('docs/*'))
    examfiles   = filter(isfile, glob('docs/examples/core/*.py'))
    examfiles.append(filter(isfile, glob('docs/examples/kernel/*.py')))
    manpages    = filter(isfile, glob('docs/man/*.1.gz'))
    igridhelpfiles = filter(isfile, glob('IPython/Extensions/igrid_help.*'))
    
    data_files = [#('data', docdirbase, docfiles),
                 ('data', pjoin(docdirbase, 'examples'),examfiles),
                 ('data', manpagebase, manpages),
                 ('data',pjoin(docdirbase, 'extensions'),igridhelpfiles),
                 ]
    # import pprint
    # pprint.pprint(data_files)
    return []

#---------------------------------------------------------------------------
# Find scripts
#---------------------------------------------------------------------------

def find_scripts():
    """
    Find IPython's scripts.
    """
    scripts = []
    scripts.append('IPython/kernel/scripts/ipengine')
    scripts.append('IPython/kernel/scripts/ipcontroller')
    scripts.append('IPython/kernel/scripts/ipcluster')
    scripts.append('scripts/ipython')
    scripts.append('scripts/pycolor')
    scripts.append('scripts/irunner')
    
    # Script to be run by the windows binary installer after the default setup
    # routine, to add shortcuts and similar windows-only things.  Windows
    # post-install scripts MUST reside in the scripts/ dir, otherwise distutils
    # doesn't find them.
    if 'bdist_wininst' in sys.argv:
        if len(sys.argv) > 2 and ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
            print >> sys.stderr,"ERROR: bdist_wininst must be run alone. Exiting."
            sys.exit(1)
        scripts.append('scripts/ipython_win_post_install.py')
    
    return scripts

#---------------------------------------------------------------------------
# Find scripts
#---------------------------------------------------------------------------

def check_for_dependencies():
    """Check for IPython's dependencies.
    
    This function should NOT be called if running under setuptools!
    """
    from setupext.setupext import (
        print_line, print_raw, print_status, print_message,
        check_for_zopeinterface, check_for_twisted,
        check_for_foolscap, check_for_pyopenssl,
        check_for_sphinx, check_for_pygments,
        check_for_nose, check_for_pexpect
    )
    print_line()
    print_raw("BUILDING IPYTHON")
    print_status('python', sys.version)
    print_status('platform', sys.platform)
    if sys.platform == 'win32':
        print_status('Windows version', sys.getwindowsversion())
    
    print_raw("")
    print_raw("OPTIONAL DEPENDENCIES")

    check_for_zopeinterface()
    check_for_twisted()
    check_for_foolscap()
    check_for_pyopenssl()
    check_for_sphinx()
    check_for_pygments()
    check_for_nose()
    check_for_pexpect()
