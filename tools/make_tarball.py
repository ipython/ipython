#!/usr/bin/env python
"""Simple script to create a tarball with proper bzr version info.
"""

import os,sys,shutil

basever = '0.9.0'

def oscmd(c):
    print ">",c
    s = os.system(c)
    if s:
        print "Error",s
        sys.exit(s)

def verinfo():
    
    out = os.popen('bzr version-info')
    pairs = (l.split(':',1) for l in out)
    d = dict(((k,v.strip()) for (k,v) in pairs)) 
    return d

basename = 'ipython'

#tarname = '%s.r%s.tgz' % (basename, ver)
oscmd('python update_revnum.py')

ver = verinfo()

if ver['branch-nick'] == 'ipython':
    tarname = 'ipython-%s.bzr.r%s.tgz' % (basever, ver['revno'])
else:
    tarname = 'ipython-%s.bzr.r%s.%s.tgz' % (basever, ver['revno'],
                                             ver['branch-nick'])
    
oscmd('bzr export ' + tarname)
