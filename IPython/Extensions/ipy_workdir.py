#!/usr/bin/env python

import IPython.ipapi
ip = IPython.ipapi.get()

import os, subprocess

workdir = None
def workdir_f(ip,line):
    """ Exceute commands residing in cwd elsewhere 
    
    Example::
      
      workdir /myfiles
      cd bin
      workdir myscript.py 
      
    executes myscript.py (stored in bin, but not in path) in /myfiles
    """
    global workdir
    dummy,cmd  = line.split(None,1)
    if os.path.isdir(cmd):
        workdir = os.path.abspath(cmd)
        print "Set workdir",workdir
    elif workdir is None:
        print "Please set workdir first by doing e.g. 'workdir q:/'"
    else:
        sp = cmd.split(None,1)
        if len(sp) == 1:
            head, tail = cmd, ''
        else:
            head, tail = sp
        if os.path.isfile(head):
            cmd = os.path.abspath(head) + ' ' + tail
        print "Execute command '" + cmd+ "' in",workdir
        olddir = os.getcwd()
        os.chdir(workdir)
        try:
            os.system(cmd)
        finally:
            os.chdir(olddir)

ip.defalias("workdir",workdir_f)
