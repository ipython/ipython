# -*- coding: utf-8 -*-
"""
%store magic for lightweight persistence.

Stores variables, aliases and macros in IPython's database.

To automatically restore stored variables at startup, add this to your
:file:`ipython_config.py` file::

  c.StoreMagic.autorestore = True
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import inspect, os, sys, textwrap

# Our own
from IPython.core.error import UsageError
from IPython.core.fakemodule import FakeModule
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.plugin import Plugin
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.traitlets import Bool, Instance

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------
    
def restore_aliases(ip):
    staliases = ip.db.get('stored_aliases', {})
    for k,v in staliases.items():
        #print "restore alias",k,v # dbg
        #self.alias_table[k] = v
        ip.alias_manager.define_alias(k,v)


def refresh_variables(ip):
    db = ip.db
    for key in db.keys('autorestore/*'):
        # strip autorestore
        justkey = os.path.basename(key)
        try:
            obj = db[key]
        except KeyError:
            print "Unable to restore variable '%s', ignoring (use %%store -d to forget!)" % justkey
            print "The error was:", sys.exc_info()[0]
        else:
            #print "restored",justkey,"=",obj #dbg
            ip.user_ns[justkey] = obj


def restore_dhist(ip):
    ip.user_ns['_dh'] = ip.db.get('dhist',[])


def restore_data(ip):
    refresh_variables(ip)
    restore_aliases(ip)
    restore_dhist(ip)


@magics_class
class StoreMagics(Magics):
    """Lightweight persistence for python variables.

    Provides the %store magic."""

    @skip_doctest
    @line_magic
    def store(self, parameter_s=''):
        """Lightweight persistence for python variables.

        Example::

          In [1]: l = ['hello',10,'world']
          In [2]: %store l
          In [3]: exit

          (IPython session is closed and started again...)

          ville@badger:~$ ipython
          In [1]: l
          Out[1]: ['hello', 10, 'world']

        Usage:

        * ``%store``          - Show list of all variables and their current
                                values
        * ``%store spam``     - Store the *current* value of the variable spam
                                to disk
        * ``%store -d spam``  - Remove the variable and its value from storage
        * ``%store -z``       - Remove all variables from storage
        * ``%store -r``       - Refresh all variables from store (delete
                                current vals)
        * ``%store foo >a.txt``  - Store value of foo to new file a.txt
        * ``%store foo >>a.txt`` - Append value of foo to file a.txt

        It should be noted that if you change the value of a variable, you
        need to %store it again if you want to persist the new value.

        Note also that the variables will need to be pickleable; most basic
        python types can be safely %store'd.

        Also aliases can be %store'd across sessions.
        """

        opts,argsl = self.parse_options(parameter_s,'drz',mode='string')
        args = argsl.split(None,1)
        ip = self.shell
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
                size = max(map(len, vars))
            else:
                size = 0

            print 'Stored variables and their in-db values:'
            fmt = '%-'+str(size)+'s -> %s'
            get = db.get
            for var in vars:
                justkey = os.path.basename(var)
                # print 30 first characters from every var
                print fmt % (justkey, repr(get(var, '<unavailable>'))[:50])

        # default action - store the variable
        else:
            # %store foo >file.txt or >>file.txt
            if len(args) > 1 and args[1].startswith('>'):
                fnam = os.path.expanduser(args[1].lstrip('>').lstrip())
                if args[1].startswith('>>'):
                    fil = open(fnam, 'a')
                else:
                    fil = open(fnam, 'w')
                obj = ip.ev(args[0])
                print "Writing '%s' (%s) to file '%s'." % (args[0],
                  obj.__class__.__name__, fnam)


                if not isinstance (obj, basestring):
                    from pprint import pprint
                    pprint(obj, fil)
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
                # This needs to be refactored to use the new AliasManager stuff.
                if args[0] in self.alias_manager:
                    name = args[0]
                    nargs, cmd = self.alias_manager.alias_table[ name ]
                    staliases = db.get('stored_aliases',{})
                    staliases[ name ] = cmd
                    db['stored_aliases'] = staliases
                    print "Alias stored: %s (%s)" % (name, cmd)
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


class StoreMagic(Plugin):
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    autorestore = Bool(False, config=True)
    
    def __init__(self, shell, config):
        super(StoreMagic, self).__init__(shell=shell, config=config)
        shell.register_magics(StoreMagics)
        
        if self.autorestore:
            restore_data(shell)


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        plugin = StoreMagic(shell=ip, config=ip.config)
        ip.plugin_manager.register_plugin('storemagic', plugin)
        _loaded = True
