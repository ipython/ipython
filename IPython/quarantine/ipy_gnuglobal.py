"""
Add %global magic for GNU Global usage.

http://www.gnu.org/software/global/

"""

from IPython.core import ipapi
ip = ipapi.get()
import os

# alter to your liking
global_bin = 'd:/opt/global/bin/global'

def global_f(self,cmdline):
    simple = 0
    if '-' not in cmdline:
        cmdline  = '-rx ' + cmdline
        simple = 1
        
    lines = [l.rstrip() for l in os.popen( global_bin + ' ' + cmdline ).readlines()]
    
    if simple:
        parts = [l.split(None,3) for l in lines]
        lines = ['%s [%s]\n%s' % (p[2].rjust(70),p[1],p[3].rstrip()) for p in parts]
    print "\n".join(lines)

ip.define_magic('global', global_f)

def global_completer(self,event):
    compl = [l.rstrip() for l in os.popen(global_bin + ' -c ' + event.symbol).readlines()]
    return compl    

ip.set_hook('complete_command', global_completer, str_key = '%global')

