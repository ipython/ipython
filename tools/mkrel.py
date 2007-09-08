""" Create ipykit and exe installer

requires py2exe

"""
#!/bin/sh
# IPython release script


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

c("python exesetup.py py2exe")

os.rename('dist',ipykit_name)

c("zip -r %s.zip %s" % (ipykit_name, ipykit_name))

c("python setup.py bdist_wininst --install-script=ipython_win_post_install.py")

os.chdir("dist")
#c("svn export http://ipython.scipy.org/svn/ipython/ipython/trunk ipython")
#c("zip -r ipython_svn.zip ipython")
