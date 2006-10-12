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

from IPython import genutils

import IPython.ipapi

class IpyPopen(Popen):
    def go(self):
        print self.communicate()[0]
    def __repr__(self):
        return '<IPython job "%s">' % self.line

def startjob(job):
    p = IpyPopen(job, stdout=PIPE)
    p.line = job
    return p

def jobctrl_prefilter_f(self,line):    
    if line.startswith('&'):
        return '_ip.startjob(%s)' % genutils.make_quoted_expr(line[1:])

    raise IPython.ipapi.TryNext

def install():
    
    ip = IPython.ipapi.get()
    # needed to make startjob visible as _ip.startjob('blah')
    ip.startjob = startjob
    ip.set_hook('input_prefilter', jobctrl_prefilter_f)     
    
install()