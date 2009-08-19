r""" %which magic command

%which <cmd> => search PATH for files matching PATH. Also scans aliases

"""

from IPython.core import ipapi
ip = ipapi.get()

import os,sys
from fnmatch import fnmatch
def which(fname):
    fullpath = filter(os.path.isdir,os.environ['PATH'].split(os.pathsep))
    
    if '.' not in fullpath:
        fullpath = ['.'] + fullpath
    fn = fname
    for p in fullpath:
        for f in os.listdir(p):
            head, ext = os.path.splitext(f)
            if f == fn or fnmatch(head, fn):
                yield os.path.join(p,f)
    return

def which_alias(fname):
    for al, tgt in ip.alias_table.items():
        if not (al == fname or fnmatch(al, fname)):
            continue
        if callable(tgt):
            print "Callable alias",tgt
            d = tgt.__doc__
            if d:
                print "Docstring:\n",d
                continue
        trg = tgt[1]
        
        trans = ip.expand_alias(trg)
        cmd = trans.split(None,1)[0]
        print al,"->",trans
        for realcmd in which(cmd):
            print "  ==",realcmd
        
def which_f(self, arg):
    r""" %which <cmd> => search PATH for files matching cmd. Also scans aliases.

    Traverses PATH and prints all files (not just executables!) that match the
    pattern on command line. Probably more useful in finding stuff
    interactively than 'which', which only prints the first matching item.
    
    Also discovers and expands aliases, so you'll see what will be executed
    when you call an alias.
    
    Example:
    
    [~]|62> %which d
    d -> ls -F --color=auto
      == c:\cygwin\bin\ls.exe
    c:\cygwin\bin\d.exe
    
    [~]|64> %which diff*
    diff3 -> diff3
      == c:\cygwin\bin\diff3.exe
    diff -> diff
      == c:\cygwin\bin\diff.exe
    c:\cygwin\bin\diff.exe
    c:\cygwin\bin\diff3.exe

    """
    
    which_alias(arg)

    for e in which(arg):
        print e
    
ip.define_magic("which",which_f)        
        
