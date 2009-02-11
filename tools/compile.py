#!/usr/bin/env python
"""Call the compile script to check that all code we ship compiles correctly.
"""

import os
import sys


vstr = '.'.join(map(str,sys.version_info[:2]))

stat = os.system('python %s/lib/python%s/compileall.py .' % (sys.prefix,vstr))

print
if stat:
    print '*** THERE WAS AN ERROR! ***'
    print 'See messages above for the actual file that produced it.'
else:
    print 'OK'

sys.exit(stat)
