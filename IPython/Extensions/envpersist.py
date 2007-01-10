# -*- coding: utf-8 -*-
"""
%store magic for lightweight persistence.

Stores variables, aliases etc. in PickleShare database.

$Id: iplib.py 1107 2006-01-30 19:02:20Z vivainio $
"""

import IPython.ipapi
ip = IPython.ipapi.get()

import os,sys

def restore_env(self):
    ip = self.getapi()
    env = ip.db.get('stored_env', {'set' : {}, 'add' : []})
    for k,v in env['set'].items():
        #print "restore alias",k,v # dbg
        os.environ[k] = v
        self.alias_table[k] = v
    for k,v in env['add']:
        os.environ[k] = os.environ.get(k,"") + v

  
ip.set_hook('late_startup_hook', restore_env)

def persist_env(self, parameter_s=''):
    """ Store environment variables persistently
    
    IPython remembers the values across sessions, which is handy to avoid 
    editing startup files.
    
    %env - Show all environment variables
    %env VISUAL=jed  - set VISUAL to jed
    %env PATH+=;/foo - append ;foo to PATH
    %env PATH+=;/foo - also append ;bar to PATH
    %env VISUAL=del  - forget VISUAL persistent val
    
    """
    
    
    
    if not parameter_s.strip():
        return os.environ.data
    
    parts = parameter_s.strip().split('=')    
    
    ip = self.getapi()
    db = ip.db
    env = ip.db.get('stored_env', {'set' : {}, 'add' : []})

    if len(parts) == 2:
        k,v = parts
        
    
    if v == 'del':
        if k in env['set']:
            del env['set'][k]
        env['add'] = [el for el in env['add'] if el[0] == k]
        #del os.environ[k]
        print "Forgot",k,"(for next session)"
        
    elif k.endswith('+'):
        k = k[:-1]
        env['add'].append((k,v))
        os.environ[k] += v
    else:
        env['set'][k] = v
        print "Setting",k,"to",v
        os.environ[k] = os.environ.get(k,"") + v
        
    db['stored_env'] = env
    

    

ip.expose_magic('env', persist_env)
