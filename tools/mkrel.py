""" Create ipykit, source package and exe installer

requires py2exe

"""
#!/bin/sh
# IPython release script


import os
import distutils.dir_util
def c(cmd):
    print ">",cmd
    os.system(cmd)

os.chdir('..')
distutils.dir_util.remove_tree('dist')
distutils.dir_util.remove_tree('ipykit')

c("python exesetup.py py2exe")
os.rename('dist','ipykit')

c("zip -r ipykit.zip ipykit")

c("python setup.py bdist_wininst --install-script=ipython_win_post_install.py")
