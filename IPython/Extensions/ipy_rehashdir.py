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

To install, add

"import_mod ext_rehashdir"

To your ipythonrc or just execute "import rehash_dir" in ipython
prompt.


$Id: InterpreterExec.py 994 2006-01-08 08:29:44Z fperez $
"""

import IPython.ipapi
ip = IPython.ipapi.get()


import os,re,fnmatch

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
    
    if not arg:
        arg = '.'
    path = map(os.path.abspath,arg.split(';'))
    alias_table = self.shell.alias_table
        
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
    savedir = os.getcwd()
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
                        print "Aliasing:",src,"->",tgt
                        alias_table[src] = (0,tgt)
        else:
            for pdir in path:
                os.chdir(pdir)
                for ff in os.listdir(pdir):
                    if isexec(ff) and not isjunk(ff):
                        src, tgt = execre.sub(r'\1',ff), os.path.abspath(ff)
                        src = src.lower()
                        print "Aliasing:",src,"->",tgt
                        alias_table[src] = (0,tgt)
        # Make sure the alias table doesn't contain keywords or builtins
        self.shell.alias_table_validate()
        # Call again init_auto_alias() so we get 'rm -i' and other
        # modified aliases since %rehashx will probably clobber them
        # self.shell.init_auto_alias()
    finally:
        os.chdir(savedir)
ip.expose_magic("rehashdir",rehashdir_f)
