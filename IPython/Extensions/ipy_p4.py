# -*- coding: utf-8 -*-
"""
Add %p4 magic for pythonic p4 (Perforce) usage.
"""

import IPython.ipapi
ip = IPython.ipapi.get()

import os,sys,marshal

import ipy_stock_completers

def p4_f(self, parameter_s=''):
    cmd = 'p4 -G ' + parameter_s
    fobj = os.popen(cmd)
    out = []
    while 1:
        try:
            out.append(marshal.load(fobj))
        except EOFError:
            break
        
    return out

def p4d(fname):
    return os.popen('p4 where ' + fname).read().split()[0]
    
ip.to_user_ns("p4d")

ip.expose_magic('p4', p4_f)

p4_commands = """\
add admin annotate branch branches change changes changelist
changelists client clients counter counters delete depot depots
describe diff diff2 dirs edit filelog files fix fixes flush fstat
group groups have help info integrate integrated job jobs jobspec
label labels labelsync lock logger login logout monitor obliterate
opened passwd print protect rename reopen resolve resolved revert
review reviews set submit sync tag tickets triggers typemap unlock
user users verify workspace workspaces where"""
    
def p4_completer(self,event):
    return ipy_stock_completers.vcs_completer(p4_commands, event)

ip.set_hook('complete_command', p4_completer, str_key = '%p4')
ip.set_hook('complete_command', p4_completer, str_key = 'p4')

