#!/usr/bin/env python
"""Simple script to create a tarball with proper bzr version info.
"""

import os
import sys
import shutil

from  toollib import *

c('python update_revnum.py')

execfile('../IPython/core/release.py')  # defines version_base

ver = version_info()

if ver['branch-nick'] == 'ipython':
    tarname = 'ipython-%s.bzr.r%s.tgz' % (version_base, ver['revno'])
else:
    tarname = 'ipython-%s.bzr.r%s.%s.tgz' % (version_base, ver['revno'],
                                             ver['branch-nick'])
    
c('bzr export ' + tarname)
