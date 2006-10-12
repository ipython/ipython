""" Preliminary "job control" extensions for IPython 

requires python 2.4 (or separate 'subprocess' module

At the moment this is in a very "unhelpful" form, will be extended in the future.

Usage:

[ipython]|2> import jobctrl
[ipython]|3> &ls
         <3> <jobctrl.IpyPopen object at 0x00D87FD0>
[ipython]|4> _3.go
-----------> _3.go()
ChangeLog
IPython
MANIFEST.in
README
README_Windows.txt

...                     
"""                     

from subprocess import Popen,PIPE
import os

from IPython import genutils

import IPython.ipapi

class IpyPopen(Popen):
    def go(self):
        print self.communicate()[0]
    def __repr__(self):
        return '<IPython job "%s" PID=%d>' % (self.line, self.pid)

    def kill(self):
        assert os.name == 'nt' # xxx add posix version 
        os.system('taskkill /PID %d' % self.pid)
                  
def startjob(job):
    p = IpyPopen(job, stdout=PIPE, shell = False)
    p.line = job
    return p

def jobctrl_prefilter_f(self,line):    
    if line.startswith('&'):
        pre,fn,rest = self.split_user_input(line[1:])
        
        line = ip.IP.expand_aliases(fn,rest)
        return '_ip.startjob(%s)' % genutils.make_quoted_expr(line)

    raise IPython.ipapi.TryNext

def install():
    global ip
    ip = IPython.ipapi.get()
    # needed to make startjob visible as _ip.startjob('blah')
    ip.startjob = startjob
    ip.set_hook('input_prefilter', jobctrl_prefilter_f)     
    
install()