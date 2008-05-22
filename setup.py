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

# Stdlib imports
import os
import sys

from glob import glob
from setupext import install_data_ext

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

if os.name == 'posix':
    os_name = 'posix'
elif os.name in ['nt','dos']:
    os_name = 'windows'
else:
    print 'Unsupported operating system:',os.name
    sys.exit(1)

# Under Windows, 'sdist' is not supported, since it requires lyxport (and
# hence lyx,perl,latex,pdflatex,latex2html,sh,...)
if os_name == 'windows' and 'sdist' in sys.argv:
    print 'The sdist command is not available under Windows.  Exiting.'
    sys.exit(1)

from distutils.core import setup

# update the manuals when building a source dist
if len(sys.argv) >= 2 and sys.argv[1] in ('sdist','bdist_rpm'):
    import textwrap
    from IPython.genutils import target_update
    # list of things to be updated. Each entry is a triplet of args for
    # target_update()
    
    def oscmd(s):
        cwd = os.getcwd()
        for l in textwrap.dedent(s).splitlines():
            print ">", l.strip()
            os.system(l.strip())
        
        os.chdir(cwd)
        
    oscmd("""\
          cd doc && python do_sphinx.py""")
    
    oscmd("cd doc && gzip -9c ipython.1 > ipython.1.gz")
    oscmd("cd doc && gzip -9c pycolor.1 > pycolor.1.gz")

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
docfiles    = filter(lambda f:file_doesnt_endwith(f,exclude),glob('doc/*'))

examfiles   = filter(isfile, glob('doc/examples/*.py'))
manfiles    = filter(isfile, glob('doc/build/html/*'))
manstatic = filter(isfile, glob('doc/build/html/_static/*'))
                     
#            filter(isfile, glob('doc/manual/*.css')) + \
#              filter(isfile, glob('doc/manual/*.png'))
              
manpages    = filter(isfile, glob('doc/*.1.gz'))
cfgfiles    = filter(isfile, glob('IPython/UserConfig/*'))
scriptfiles = filter(isfile, ['scripts/ipython','scripts/pycolor',
                              'scripts/irunner'])
igridhelpfiles = filter(isfile, glob('IPython/Extensions/igrid_help.*'))

# Script to be run by the windows binary installer after the default setup
# routine, to add shortcuts and similar windows-only things.  Windows
# post-install scripts MUST reside in the scripts/ dir, otherwise distutils
# doesn't find them.
if 'bdist_wininst' in sys.argv:
    if len(sys.argv) > 2 and ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
        print >> sys.stderr,"ERROR: bdist_wininst must be run alone. Exiting."
        sys.exit(1)
    scriptfiles.append('scripts/ipython_win_post_install.py')

datafiles = [('data', docdirbase, docfiles),
             ('data', pjoin(docdirbase, 'examples'),examfiles),
             ('data', pjoin(docdirbase, 'manual'),manfiles),
             ('data', pjoin(docdirbase, 'manual/_static'),manstatic),
             ('data', manpagebase, manpages),
             ('data',pjoin(docdirbase, 'extensions'),igridhelpfiles),
             ]

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
    # eggs will lack docs, eaxmples
    datafiles = []
    
    #datafiles = [('lib', 'IPython/UserConfig', cfgfiles)]
else:
    egg_extra_kwds = {}
    # package_data of setuptools was introduced to distutils in 2.4
    if sys.version_info < (2,4):
        datafiles.append(('lib', 'IPython/UserConfig', cfgfiles))
    
    


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
      packages         = ['IPython', 'IPython.Extensions', 'IPython.external', 'IPython.gui', 'IPython.gui.wx', 'IPython.UserConfig'],
      scripts          = scriptfiles,
      package_data     = {'IPython.UserConfig' : ['*'] },
      
      cmdclass         = {'install_data': install_data_ext},
      data_files       = datafiles,
      # extra params needed for eggs
      **egg_extra_kwds                        
      )
