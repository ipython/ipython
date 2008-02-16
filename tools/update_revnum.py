#!/usr/bin/env python
""" Change the revision number in Release.py """

import os
import re

rev = os.popen('svnversion ..').read().strip()

print "current rev is",rev
assert ':' not in rev

rfile = open('../IPython/Release.py').read()
newcont = re.sub(r'revision\s*=.*', "revision = '%s'" % rev, rfile)
open('../IPython/Release.py','w').write(newcont)
