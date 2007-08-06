#!/bin/sh
# IPython release script

import os
import distutils.dir_util
def c(cmd):
    print ">",cmd
    os.system(cmd)

os.chdir('..')

distutils.dir_util.remove_tree('dist')


c("python setup.py bdist_wininst --install-script=ipython_win_post_install.py")
c("python exesetup.py py2exe")
