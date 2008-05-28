#!/usr/bin/env python
"""IPython release script

Create ipykit and exe installer

requires py2exe
"""

import os
import distutils.dir_util
import sys

execfile('../IPython/Release.py')

def c(cmd):
    print ">",cmd
    os.system(cmd)

ipykit_name = "ipykit-%s" % version

os.chdir('..')
if os.path.isdir('dist'):
    distutils.dir_util.remove_tree('dist')
if os.path.isdir(ipykit_name):
    distutils.dir_util.remove_tree(ipykit_name)

if sys.platform == 'win32':
    c("python exesetup.py py2exe")

    os.rename('dist',ipykit_name)

    c("zip -r %s.zip %s" % (ipykit_name, ipykit_name))

# Build source and binary distros
c('./setup.py sdist --formats=gztar')

c("python2.4 ./setup.py bdist_rpm --binary-only --release=py24 --python=/usr/bin/python2.4")
c("python2.5 ./setup.py bdist_rpm --binary-only --release=py25 --python=/usr/bin/python2.5")

# Build eggs
c('python2.4 ./eggsetup.py bdist_egg')
c('python2.5 ./eggsetup.py bdist_egg')

c("python setup.py bdist_wininst --install-script=ipython_win_post_install.py")

os.chdir('tools')
c('python make_tarball.py')

