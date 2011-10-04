# -*- coding: utf-8 -*-
""" %env magic command for storing environment variables persistently
"""

from IPython.core import ipapi
from IPython.core.error import TryNext

ip = ipapi.get()

import os,sys

def restore_env(self):
    ip = self.getapi()
    env = ip.db.get('stored_env', {'set' : {}, 'add' : [], 'pre' : []})
    for k,v in env['set'].items():
        os.environ[k] = v
    for k,v in env['add']:
        os.environ[k] = os.environ.get(k,"") + v
    for k,v in env['pre']:
        os.environ[k] = v + os.environ.get(k,"")
    raise TryNext

ip.set_hook('late_startup_hook', restore_env)

def persist_env(self, parameter_s=''):
    """ Store environment variables persistently

    IPython remembers the values across sessions, which is handy to avoid
    editing startup files.

    %env - Show all environment variables
    %env VISUAL=jed  - set VISUAL to jed
    %env PATH+=;/foo - append ;foo to PATH
    %env PATH+=;/bar - also append ;bar to PATH
    %env PATH-=/wbin; - prepend /wbin; to PATH
    %env -d VISUAL   - forget VISUAL persistent val
    %env -p          - print all persistent env modifications
    """

    if not parameter_s.strip():
        return os.environ.data

    ip = self.getapi()
    db = ip.db
    env = ip.db.get('stored_env', {'set' : {}, 'add' : [], 'pre' : []})

    if parameter_s.startswith('-p'):
        return env

    elif parameter_s.startswith('-d'):
        parts = (parameter_s.split()[1], '<del>')

    else:
        parts = parameter_s.strip().split('=')

    if len(parts) == 2:
        k,v = [p.strip() for p in parts]

    if v == '<del>':
        if k in env['set']:
            del env['set'][k]
        env['add'] = [el for el in env['add'] if el[0] != k]
        env['pre'] = [el for el in env['pre'] if el[0] != k]

        print "Forgot '%s' (for next session)" % k

    elif k.endswith('+'):
        k = k[:-1]
        env['add'].append((k,v))
        os.environ[k] += v
        print k,"after append =",os.environ[k]
    elif k.endswith('-'):
        k = k[:-1]
        env['pre'].append((k,v))
        os.environ[k] = v + os.environ.get(k,"")
        print k,"after prepend =",os.environ[k]


    else:
        env['set'][k] = v
        print "Setting",k,"to",v
        os.environ[k] = v

    db['stored_env'] = env

def env_completer(self,event):
    """ Custom completer that lists all env vars """
    return os.environ.keys()

ip.define_magic('env', persist_env)
ip.set_hook('complete_command',env_completer, str_key = '%env')

