# -*- coding: utf-8 -*-
"""
%jot magic for lightweight persistence.

Stores variables in Struct with some notes in PicleShare database


"""

from datetime import datetime
from IPython.core import ipapi
ip = ipapi.get()

import pickleshare

import inspect,pickle,os,sys,textwrap
from IPython.core.fakemodule import FakeModule
from IPython.utils.ipstruct import Struct
from IPython.utils.warn import error


def refresh_variables(ip, key=None):
    db = ip.db
    if key is None:
        keys = db.keys('jot/*')
    else:
        keys = db.keys('jot/'+key)
    for key in keys:
        # strip autorestore
        justkey = os.path.basename(key)
        print "Restoring from", justkey, "..."
        try:
            obj = db[key]
        except KeyError:
            print "Unable to restore variable '%s', ignoring (use %%jot -d to forget!)" % justkey
            print "The error was:",sys.exc_info()[0]
        else:
            #print "restored",justkey,"=",obj #dbg
            try:
                origname = obj.name
            except:
                ip.user_ns[justkey] = obj
                print "Restored", justkey
            else:
                ip.user_ns[origname] = obj['val']
                print "Restored", origname

def read_variables(ip, key=None):
    db = ip.db
    if key is None:
        return None
    else:
        keys = db.keys('jot/'+key)
    for key in keys:
        # strip autorestore
        justkey = os.path.basename(key)
        print "restoring from ", justkey
        try:
            obj = db[key]
        except KeyError:
            print "Unable to read variable '%s', ignoring (use %%jot -d to forget!)" % justkey
            print "The error was:",sys.exc_info()[0]
        else:
            return obj


def detail_variables(ip, key=None):
    db, get = ip.db, ip.db.get

    if key is None:
        keys = db.keys('jot/*')
    else:
        keys = db.keys('jot/'+key)
    if keys:
        size = max(map(len,keys))
    else:
        size = 0

    fmthead = '%-'+str(size)+'s [%s]'
    fmtbody = 'Comment:\n %s'
    fmtdata = 'Data:\n %s, %s'
    for key in keys:
        v = get(key,'<unavailable>')
        justkey = os.path.basename(key)
        try:
            print fmthead % (justkey, datetime.ctime(v.get('time','<unavailable>')))
            print fmtbody % (v.get('comment','<unavailable>'))
            d = v.get('val','unavailable')
            print fmtdata % (repr(type(d)), '')
            print repr(d)[0:200]
            print
            print
        except AttributeError:
            print fmt % (justkey, '<unavailable>', '<unavailable>', repr(v)[:50])


def intm(n):
    try:
        return int(n)
    except:
        return 0

def jot_obj(self, obj, name, comment=''):
    """
    write obj data to the note database, with whatever that should be noted.
    """
    had = self.db.keys('jot/'+name+'*')
    # if it the same name but a later version, we stupidly add a number to the
    # so the name doesn't collide. Any better idea?
    suffix = ''
    if len(had)>0:
        pre = os.path.commonprefix(had)
        suf = [n.split(pre)[1] for n in had]
        versions = map(intm, suf)
        suffix = str(max(versions)+1)

    uname = 'jot/'+name+suffix

    all = ip.shell.history_manager.input_hist_parsed

    # We may actually want to make snapshot of files that are run-ned.

    # get the comment
    try:
        comment = ip.magic_edit('-x').strip()
    except:
        print "No comment is recorded."
        comment = ''

    self.db[uname] = Struct({'val':obj,
                'time'  :   datetime.now(),
                'hist'  :   all,
                'name'  :   name,
                'comment' : comment,})

    print "Jotted down notes for '%s' (%s)" % (uname, obj.__class__.__name__)



def magic_jot(self, parameter_s=''):
    """Lightweight persistence for python variables.

    Example:

    ville@badger[~]|1> A = ['hello',10,'world']\\
    ville@badger[~]|2> %jot A\\
    ville@badger[~]|3> Exit

    (IPython session is closed and started again...)

    ville@badger:~$ ipython -p pysh\\
    ville@badger[~]|1> print A

    ['hello', 10, 'world']

    Usage:

    %jot          - Show list of all variables and their current values\\
    %jot -l       - Show list of all variables and their current values in detail\\
    %jot -l <var> - Show one variable and its current values in detail\\
    %jot <var>    - Store the *current* value of the variable to disk\\
    %jot -d <var> - Remove the variable and its value from storage\\
    %jot -z       - Remove all variables from storage (disabled)\\
    %jot -r <var> - Refresh/Load variable from jot (delete current vals)\\
    %jot foo >a.txt  - Store value of foo to new file a.txt\\
    %jot foo >>a.txt - Append value of foo to file a.txt\\

    It should be noted that if you change the value of a variable, you
    need to %note it again if you want to persist the new value.

    Note also that the variables will need to be pickleable; most basic
    python types can be safely %stored.

    """

    opts,argsl = self.parse_options(parameter_s,'drzl',mode='string')
    args = argsl.split(None,1)
    ip = self.getapi()
    db = ip.db
    # delete
    if opts.has_key('d'):
        try:
            todel = args[0]
        except IndexError:
            error('You must provide the variable to forget')
        else:
            try:
                del db['jot/' + todel]
            except:
                error("Can't delete variable '%s'" % todel)
    # reset the whole database
    elif opts.has_key('z'):
        print "reseting the whole database has been disabled."
        #for k in db.keys('autorestore/*'):
        #    del db[k]

    elif opts.has_key('r'):
        try:
            toret = args[0]
        except:
            print "restoring all the variables jotted down..."
            refresh_variables(ip)
        else:
            refresh_variables(ip, toret)

    elif opts.has_key('l'):
        try:
            tolist = args[0]
        except:
            print "List details for all the items."
            detail_variables(ip)
        else:
            print "Details for", tolist, ":"
            detail_variables(ip, tolist)

    # run without arguments -> list noted variables & notes
    elif not args:
        vars = self.db.keys('jot/*')
        vars.sort()
        if vars:
            size = max(map(len,vars)) - 4
        else:
            size = 0

        print 'Variables and their in-db values:'
        fmt = '%-'+str(size)+'s [%s] -> %s'
        get = db.get
        for var in vars:
            justkey = os.path.basename(var)
            v = get(var,'<unavailable>')
            try:
                print fmt % (justkey,\
                    datetime.ctime(v.get('time','<unavailable>')),\
                    v.get('comment','<unavailable>')[:70].replace('\n',' '),)
            except AttributeError:
                print fmt % (justkey, '<unavailable>', '<unavailable>', repr(v)[:50])


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

        # %note foo
        try:
            obj = ip.user_ns[args[0]]
        except KeyError:
            # this should not be alias, for aliases, use %store
            print
            print "Error: %s doesn't exist." % args[0]
            print
            print "Use %note -r <var> to retrieve variables. This should not be used " +\
                  "to store alias, for saving aliases, use %store"
            return
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
            #self.db[ 'jot/' + args[0] ] = obj
            jot_obj(self, obj, args[0])


def magic_read(self, parameter_s=''):
    """
    %read <var> - Load variable from data that is jotted down.\\

    """

    opts,argsl = self.parse_options(parameter_s,'drzl',mode='string')
    args = argsl.split(None,1)
    ip = self.getapi()
    db = ip.db
    #if opts.has_key('r'):
    try:
        toret = args[0]
    except:
        print "which record do you want to read out?"
        return
    else:
        return read_variables(ip, toret)


ip.define_magic('jot',magic_jot)
ip.define_magic('read',magic_read)
