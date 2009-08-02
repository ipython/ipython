#!/usr/bin/env python
"""Change the revision number in Release.py

This edits in-place Release.py to update the revision number from bzr info. 

Usage:

./update_revnum.py"""

import os
import pprint
import re

from toollib import *

if __name__ == '__main__':
    ver = version_info()

    pprint.pprint(ver)

    rfile = open('../IPython/Release.py','rb').read()
    newcont = re.sub(r'revision\s*=.*',
                     "revision = '%s'" % ver['revno'],
                     rfile)

    newcont = re.sub(r'^branch\s*=[^=].*',
                     "branch = '%s'"  % ver['branch-nick'],
                     newcont)

    f = open('../IPython/Release.py','wb')
    f.write(newcont)
    f.close()
