#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Setup script for exe distribution of IPython (does not require python).

- Requires py2exe

- install pyreadline *package dir* in ipython root directory by running:
  
svn co http://ipython.scipy.org/svn/ipython/pyreadline/branches/maintenance_1.3/pyreadline/  
wget http://ipython.scipy.org/svn/ipython/pyreadline/branches/maintenance_1.3/readline.py

OR (if you want the latest trunk):  
  
svn co http://ipython.scipy.org/svn/ipython/pyreadline/trunk/pyreadline

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
from distutils import dir_util
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


egg_extra_kwds = {}

# Call the setup() routine which does most of the work
setup(name             = name,
    options   = {
    'py2exe': {
        'packages' : ['IPython', 'IPython.Extensions', 'IPython.external',
                      'pyreadline'],
        'excludes' : ["Tkconstants","Tkinter","tcl",'IPython.igrid','wx',
                      'wxPython','igrid', 'PyQt4', 'zope', 'Zope', 'Zope2',
                      '_curses','enthought.traits','gtk','qt', 'pydb','idlelib',                      
                      ]
                    
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
    console          = ['ipykit.py'],
    
    # extra params needed for eggs
    **egg_extra_kwds                        
    )

minimal_conf = """
import IPython.ipapi
ip = IPython.ipapi.get()

ip.load('ipy_kitcfg')
import ipy_profile_sh
"""

if not os.path.isdir("dist/_ipython"):
    print "Creating simple _ipython dir"
    os.mkdir("dist/_ipython")
    open("dist/_ipython/ipythonrc.ini","w").write("# intentionally blank\n")
    open("dist/_ipython/ipy_user_conf.py","w").write(minimal_conf)
    if os.path.isdir('bin'):
        dir_util.copy_tree('bin','dist/bin')
