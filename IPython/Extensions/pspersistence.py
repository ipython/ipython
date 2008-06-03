# -*- coding: utf-8 -*-
"""
%store magic for lightweight persistence.

Stores variables, aliases etc. in PickleShare database.

$Id: iplib.py 1107 2006-01-30 19:02:20Z vivainio $
"""

import IPython.ipapi
from IPython.ipapi import UsageError
ip = IPython.ipapi.get()

import pickleshare

import inspect,pickle,os,sys,textwrap
from IPython.FakeModule import FakeModule

def restore_aliases(self):
    ip = self.getapi()
    staliases = ip.db.get('stored_aliases', {})
    for k,v in staliases.items():
        #print "restore alias",k,v # dbg
        #self.alias_table[k] = v
        ip.defalias(k,v)


def refresh_variables(ip):
    db = ip.db
    for key in db.keys('autorestore/*'):
        # strip autorestore
        justkey = os.path.basename(key)
        try:
            obj = db[key]
        except KeyError:
            print "Unable to restore variable '%s', ignoring (use %%store -d to forget!)" % justkey
            print "The error was:",sys.exc_info()[0]
        else:
            #print "restored",justkey,"=",obj #dbg
            ip.user_ns[justkey] = obj
    

def restore_dhist(ip):
    db = ip.db
    ip.user_ns['_dh'] = db.get('dhist',[])
    
def restore_data(self):
    ip = self.getapi()
    refresh_variables(ip)
    restore_aliases(self)
    restore_dhist(self)
    raise IPython.ipapi.TryNext
    
ip.set_hook('late_startup_hook', restore_data)

def magic_store(self, parameter_s=''):
    """Lightweight persistence for python variables.

    Example:
    
    ville@badger[~]|1> A = ['hello',10,'world']\\
    ville@badger[~]|2> %store A\\
    ville@badger[~]|3> Exit
    
    (IPython session is closed and started again...)
    
    ville@badger:~$ ipython -p pysh\\
    ville@badger[~]|1> print A
    
    ['hello', 10, 'world']
    
    Usage:
    
    %store          - Show list of all variables and their current values\\
    %store <var>    - Store the *current* value of the variable to disk\\
    %store -d <var> - Remove the variable and its value from storage\\
    %store -z       - Remove all variables from storage\\
    %store -r       - Refresh all variables from store (delete current vals)\\
    %store foo >a.txt  - Store value of foo to new file a.txt\\
    %store foo >>a.txt - Append value of foo to file a.txt\\   
    
    It should be noted that if you change the value of a variable, you
    need to %store it again if you want to persist the new value.
    
    Note also that the variables will need to be pickleable; most basic
    python types can be safely %stored.
    
    Also aliases can be %store'd across sessions.
    """
    
    opts,argsl = self.parse_options(parameter_s,'drz',mode='string')
    args = argsl.split(None,1)
    ip = self.getapi()
    db = ip.db
    # delete
    if opts.has_key('d'):
        try:
            todel = args[0]
        except IndexError:
            raise UsageError('You must provide the variable to forget')
        else:
            try:
                del db['autorestore/' + todel]
            except:
                raise UsageError("Can't delete variable '%s'" % todel)
    # reset
    elif opts.has_key('z'):
        for k in db.keys('autorestore/*'):
            del db[k]

    elif opts.has_key('r'):
        refresh_variables(ip)

    
    # run without arguments -> list variables & values
    elif not args:
        vars = self.db.keys('autorestore/*')
        vars.sort()            
        if vars:
            size = max(map(len,vars))
        else:
            size = 0
            
        print 'Stored variables and their in-db values:'
        fmt = '%-'+str(size)+'s -> %s'
        get = db.get
        for var in vars:
            justkey = os.path.basename(var)
            # print 30 first characters from every var
            print fmt % (justkey,repr(get(var,'<unavailable>'))[:50])
    
    # default action - store the variable
    else:
        # %store foo >file.txt or >>file.txt
        if len(args) > 1 and args[1].startswith('>'):
            fnam = os.path.expanduser(args[1].lstrip('>').lstrip())
            if args[1].startswith('>>'):
                fil = open(fnam,'a')
            else:
                fil = open(fnam,'w')
            obj = ip.ev(args[0])
            print "Writing '%s' (%s) to file '%s'." % (args[0],
              obj.__class__.__name__, fnam)

            
            if not isinstance (obj,basestring):
                from pprint import pprint
                pprint(obj,fil)
            else:
                fil.write(obj)
                if not obj.endswith('\n'):
                    fil.write('\n')
            
            fil.close()
            return
        
        # %store foo
        try:
            obj = ip.user_ns[args[0]]
        except KeyError:
            # it might be an alias
            if args[0] in self.alias_table:
                staliases = db.get('stored_aliases',{})
                staliases[ args[0] ] = self.alias_table[ args[0] ]
                db['stored_aliases'] = staliases                
                print "Alias stored:", args[0], self.alias_table[ args[0] ]
                return
            else:
                raise UsageError("Unknown variable '%s'" % args[0])
            
        else:
            if isinstance(inspect.getmodule(obj), FakeModule):
                print textwrap.dedent("""\
                Warning:%s is %s 
                Proper storage of interactively declared classes (or instances
                of those classes) is not possible! Only instances
                of classes in real modules on file system can be %%store'd.
                """ % (args[0], obj) ) 
                return
            #pickled = pickle.dumps(obj)
            self.db[ 'autorestore/' + args[0] ] = obj
            print "Stored '%s' (%s)" % (args[0], obj.__class__.__name__)

ip.expose_magic('store',magic_store)
