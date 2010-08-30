#!/usr/bin/env python
"""Change the revision number in release.py

This edits in-place release.py to update the revision number from bzr info. 

Usage:

./update_revnum.py"""

import os
import re

from toollib import *

if __name__ == '__main__':
    # definges branch, revision, version_base
    execfile('../IPython/core/release.py')

    rfile = open('../IPython/core/release.py','rb').read()
    newcont = re.sub(r'\nrevision\s*=.*',
                     "\nrevision = '%s'" % revision,
                     rfile)

    newcont = re.sub(r'\nbranch\s*=[^=].*',
                     "\nbranch = '%s'"  % branch,
                     newcont)

    newcont = re.sub(r'\ndevelopment\s*=[^=].*',
                     "\ndevelopment = False",
                     newcont)

    f = open('../IPython/core/release.py','wb')
    f.write(newcont)
    f.close()
