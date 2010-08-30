#!/usr/bin/env python
"""Simple script to create a tarball with proper git version info.
"""

import os
import sys
import shutil

from  toollib import *

c('python update_revnum.py')

# definges branch, revision, version_base
execfile('../IPython/core/release.py')

if branch == 'master':
    tarname = 'ipython-%s.git.%s.tar.xz' % (version_base, revision[:7])
else:
    tarname = 'ipython-%s.git.%s.%s.tar.xz' % (version_base, revision[:7],
                                             branch)

pwd = os.path.abspath(os.path.curdir)
os.chdir('..')
c('git archive --format=tar --prefix=ipython-%s/ %s |  xz -z --force - > %s'
    % (version_base, revision, pwd+os.sep+tarname) )
