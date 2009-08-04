#!/usr/bin/env python
"""Change the revision number in release.py

This edits in-place release.py to update the revision number from bzr info. 

Usage:

./update_revnum.py"""

import os
import pprint
import re

from toollib import *

if __name__ == '__main__':
    ver = version_info()

    pprint.pprint(ver)

    rfile = open('../IPython/core/release.py','rb').read()
    newcont = re.sub(r'revision\s*=.*',
                     "revision = '%s'" % ver['revno'],
                     rfile)

    newcont = re.sub(r'^branch\s*=[^=].*',
                     "branch = '%s'"  % ver['branch-nick'],
                     newcont)

    f = open('../IPython/core/release.py','wb')
    f.write(newcont)
    f.close()
