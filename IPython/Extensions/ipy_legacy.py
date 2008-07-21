""" Legacy stuff

Various stuff that are there for historical / familiarity reasons.

This is automatically imported by default profile, though not other profiles
(e.g. 'sh' profile).

Stuff that is considered obsolete / redundant is gradually moved here.

"""

import IPython.ipapi
ip = IPython.ipapi.get()

import os,sys

from IPython.genutils import *

# use rehashx

def magic_rehash(self, parameter_s = ''):
    """Update the alias table with all entries in $PATH.

    This version does no checks on execute permissions or whether the
    contents of $PATH are truly files (instead of directories or something
    else).  For such a safer (but slower) version, use %rehashx."""

    # This function (and rehashx) manipulate the alias_table directly
    # rather than calling magic_alias, for speed reasons.  A rehash on a
    # typical Linux box involves several thousand entries, so efficiency
    # here is a top concern.

    path = filter(os.path.isdir,os.environ.get('PATH','').split(os.pathsep))
    alias_table = self.shell.alias_table
    for pdir in path:
        for ff in os.listdir(pdir):
            # each entry in the alias table must be (N,name), where
            # N is the number of positional arguments of the alias.
            alias_table[ff] = (0,ff)
    # Make sure the alias table doesn't contain keywords or builtins
    self.shell.alias_table_validate()
    # Call again init_auto_alias() so we get 'rm -i' and other modified
    # aliases since %rehash will probably clobber them
    self.shell.init_auto_alias()

ip.expose_magic("rehash", magic_rehash)

# Exit
def magic_Quit(self, parameter_s=''):
    """Exit IPython without confirmation (like %Exit)."""

    self.shell.ask_exit()

ip.expose_magic("Quit", magic_Quit)


# make it autocallable fn if you really need it
def magic_p(self, parameter_s=''):
    """Just a short alias for Python's 'print'."""
    exec 'print ' + parameter_s in self.shell.user_ns

ip.expose_magic("p", magic_p)
