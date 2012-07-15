# -*- coding: utf-8 -*-
""" IPython extension: add %rehashdir magic

Usage:

%rehashdir c:/bin c:/tools
  - Add all executables under c:/bin and c:/tools to alias table, in
  order to make them directly executable from any directory.

This also serves as an example on how to extend ipython
with new magic functions.

Unlike rest of ipython, this requires Python 2.4 (optional
extensions are allowed to do that).

"""

from IPython.core import ipapi
ip = ipapi.get()


import os,re,fnmatch,sys

def selflaunch(ip,line):
    """ Launch python script with 'this' interpreter

    e.g. d:\foo\ipykit.exe a.py

    """

    tup = line.split(None,1)
    if len(tup) == 1:
        print "Launching nested ipython session"
        os.system(sys.executable)
        return

    cmd = sys.executable + ' ' + tup[1]
    print ">",cmd
    os.system(cmd)

class PyLauncher:
    """ Invoke selflanucher on the specified script

    This is mostly useful for associating with scripts using::
        _ip.define_alias('foo',PyLauncher('foo_script.py'))

    """
    def __init__(self,script):
        self.script = os.path.abspath(script)
    def __call__(self, ip, line):
        if self.script.endswith('.ipy'):
            ip.runlines(open(self.script).read())
        else:
            # first word is the script/alias name itself, strip it
            tup = line.split(None,1)
            if len(tup) == 2:
                tail = ' ' + tup[1]
            else:
                tail = ''

            selflaunch(ip,"py " + self.script + tail)
    def __repr__(self):
        return 'PyLauncher("%s")' % self.script

def rehashdir_f(self,arg):
    """ Add executables in all specified dirs to alias table

    Usage:

    %rehashdir c:/bin;c:/tools
      - Add all executables under c:/bin and c:/tools to alias table, in
      order to make them directly executable from any directory.

      Without arguments, add all executables in current directory.

    """

    # most of the code copied from Magic.magic_rehashx

    def isjunk(fname):
        junk = ['*~']
        for j in junk:
            if fnmatch.fnmatch(fname, j):
                return True
        return False

    created = []
    if not arg:
        arg = '.'
    path = map(os.path.abspath,arg.split(';'))
    alias_table = self.shell.alias_manager.alias_table

    if os.name == 'posix':
        isexec = lambda fname:os.path.isfile(fname) and \
                 os.access(fname,os.X_OK)
    else:

        try:
            winext = os.environ['pathext'].replace(';','|').replace('.','')
        except KeyError:
            winext = 'exe|com|bat|py'
        if 'py' not in winext:
            winext += '|py'

        execre = re.compile(r'(.*)\.(%s)$' % winext,re.IGNORECASE)
        isexec = lambda fname:os.path.isfile(fname) and execre.match(fname)
    savedir = os.getcwdu()
    try:
        # write the whole loop for posix/Windows so we don't have an if in
        # the innermost part
        if os.name == 'posix':
            for pdir in path:
                os.chdir(pdir)
                for ff in os.listdir(pdir):
                    if isexec(ff) and not isjunk(ff):
                        # each entry in the alias table must be (N,name),
                        # where N is the number of positional arguments of the
                        # alias.
                        src,tgt = os.path.splitext(ff)[0], os.path.abspath(ff)
                        created.append(src)
                        alias_table[src] = (0,tgt)
        else:
            for pdir in path:
                os.chdir(pdir)
                for ff in os.listdir(pdir):
                    if isexec(ff) and not isjunk(ff):
                        src, tgt = execre.sub(r'\1',ff), os.path.abspath(ff)
                        src = src.lower()
                        created.append(src)
                        alias_table[src] = (0,tgt)
        # Make sure the alias table doesn't contain keywords or builtins
        self.shell.alias_table_validate()
        # Call again init_auto_alias() so we get 'rm -i' and other
        # modified aliases since %rehashx will probably clobber them
        # self.shell.init_auto_alias()
    finally:
        os.chdir(savedir)
    return created

ip.define_magic("rehashdir",rehashdir_f)
