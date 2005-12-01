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
if os_name == 'windows' and sys.argv[1] == 'sdist':
    print 'The sdist command is not available under Windows.  Exiting.'
    sys.exit(1)

from distutils.core import setup

# update the manuals when building a source dist
if len(sys.argv) >= 2 and sys.argv[1] in ('sdist','bdist_rpm'):
    from IPython.genutils import target_update
    # list of things to be updated. Each entry is a triplet of args for
    # target_update()
    to_update = [('doc/magic.tex',
                  ['IPython/Magic.py'],
                  "cd doc && ./update_magic.sh" ),
                 
                 ('doc/manual.lyx',
                  ['IPython/Release.py','doc/manual_base.lyx'],
                  "cd doc && ./update_version.sh" ),
                 
                 ('doc/manual/manual.html',
                  ['doc/manual.lyx',
                   'doc/magic.tex',
                   'doc/examples/example-gnuplot.py',
                   'doc/examples/example-magic.py',
                   'doc/examples/example-embed.py',
                   'doc/examples/example-embed-short.py',
                   'IPython/UserConfig/ipythonrc',
                   ],
                  "cd doc && "
                  "lyxport -tt --leave --pdf "
                  "--html -o '-noinfo -split +1 -local_icons' manual.lyx"),
                 
                 ('doc/new_design.pdf',
                  ['doc/new_design.lyx'],
                  "cd doc && lyxport -tt --pdf new_design.lyx"),

                 ('doc/ipython.1.gz',
                  ['doc/ipython.1'],
                  "cd doc && gzip -9c ipython.1 > ipython.1.gz"),

                 ('doc/pycolor.1.gz',
                  ['doc/pycolor.1'],
                  "cd doc && gzip -9c pycolor.1 > pycolor.1.gz"),
                 ]
    for target in to_update:
        target_update(*target)

# Release.py contains version, authors, license, url, keywords, etc.
execfile(os.path.join('IPython','Release.py'))

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
docdirbase  = 'share/doc/ipython-%s' % version
manpagebase = 'share/man/man1'

# We only need to exclude from this things NOT already excluded in the
# MANIFEST.in file.
exclude     = ('.sh','.1.gz')
docfiles    = filter(lambda f:file_doesnt_endwith(f,exclude),glob('doc/*'))

examfiles   = filter(isfile, glob('doc/examples/*.py'))
manfiles    = filter(isfile, glob('doc/manual/*.html')) + \
              filter(isfile, glob('doc/manual/*.css')) + \
              filter(isfile, glob('doc/manual/*.png'))
manpages    = filter(isfile, glob('doc/*.1.gz'))
cfgfiles    = filter(isfile, glob('IPython/UserConfig/*'))
scriptfiles = filter(isfile, ['scripts/ipython','scripts/pycolor'])

# Script to be run by the windows binary installer after the default setup
# routine, to add shortcuts and similar windows-only things.  Windows
# post-install scripts MUST reside in the scripts/ dir, otherwise distutils
# doesn't find them.
if 'bdist_wininst' in sys.argv:
    if len(sys.argv) > 2 and ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
        print >> sys.stderr,"ERROR: bdist_wininst must be run alone. Exiting."
        sys.exit(1)
    scriptfiles.append('scripts/ipython_win_post_install.py')

# Call the setup() routine which does most of the work
setup(name             = name,
      version          = version,
      description      = description,
      long_description = long_description,
      author           = authors['Fernando'][0],
      author_email     = authors['Fernando'][1],
      url              = url,
      license          = license,
      platforms        = platforms,
      keywords         = keywords,
      packages         = ['IPython', 'IPython.Extensions'],
      scripts          = scriptfiles,
      cmdclass         = {'install_data': install_data_ext},
      data_files       = [('data', docdirbase, docfiles),
                          ('data', os.path.join(docdirbase, 'examples'),
                           examfiles),
                          ('data', os.path.join(docdirbase, 'manual'),
                           manfiles),
                          ('data', manpagebase, manpages),
                          ('lib', 'IPython/UserConfig', cfgfiles)]
      )
