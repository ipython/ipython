#!/usr/bin/env python
""" Change the revision number in Release.py """

import os
import re,pprint

def verinfo():
    
    out = os.popen('bzr version-info')
    pairs = (l.split(':',1) for l in out)
    d = dict(((k,v.strip()) for (k,v) in pairs)) 
    return d

ver = verinfo()

pprint.pprint(ver)

rfile = open('../IPython/Release.py','rb').read()
newcont = re.sub(r'revision\s*=.*', "revision = '%s'" % ver['revno'], rfile)

newcont = re.sub(r'^branch\s*=[^=].*', "branch = '%s'"  % ver['branch-nick'], newcont )

open('../IPython/Release.py','wb').write(newcont)
