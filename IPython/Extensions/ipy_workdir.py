#!/usr/bin/env python

import IPython.ipapi
ip = IPython.ipapi.get()

import os, subprocess

workdir = None
def workdir_f(line):
    global workdir
    dummy,cmd  = line.split(None,1)
    if os.path.isdir(cmd):
        workdir = cmd
        print "Set workdir",workdir
    elif workdir is None:
        print "Please set workdir first by doing e.g. 'workdir q:/'"
    else:
        print "Execute command in",workdir
        ret = subprocess.call(cmd, shell = True, cwd = workdir)

ip.defalias("workdir",workdir_f)
        
        
        
    

