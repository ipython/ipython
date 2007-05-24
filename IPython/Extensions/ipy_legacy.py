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

# use ?
def magic_pdef(self, parameter_s='', namespaces=None):
    """Print the definition header for any callable object.

    If the object is a class, print the constructor information."""
    self._inspect('pdef',parameter_s, namespaces)

ip.expose_magic("pdef", magic_pdef)        

# use ?    
def magic_pdoc(self, parameter_s='', namespaces=None):
    """Print the docstring for an object.

    If the given object is a class, it will print both the class and the
    constructor docstrings."""
    self._inspect('pdoc',parameter_s, namespaces)

ip.expose_magic("pdoc", magic_pdoc)        

# use ??
def magic_psource(self, parameter_s='', namespaces=None):
    """Print (or run through pager) the source code for an object."""
    self._inspect('psource',parameter_s, namespaces)

ip.expose_magic("pdoc", magic_psource)

# use ?
def magic_pfile(self, parameter_s=''):
    """Print (or run through pager) the file where an object is defined.

    The file opens at the line where the object definition begins. IPython
    will honor the environment variable PAGER if set, and otherwise will
    do its best to print the file in a convenient form.

    If the given argument is not an object currently defined, IPython will
    try to interpret it as a filename (automatically adding a .py extension
    if needed). You can thus use %pfile as a syntax highlighting code
    viewer."""

    # first interpret argument as an object name
    out = self._inspect('pfile',parameter_s)
    # if not, try the input as a filename
    if out == 'not found':
        try:
            filename = get_py_filename(parameter_s)
        except IOError,msg:
            print msg
            return
        page(self.shell.inspector.format(file(filename).read()))

ip.expose_magic("pfile", magic_pfile)        

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

#use cd -<tab>
def magic_dhist(self, parameter_s=''):
    """Print your history of visited directories.

    %dhist       -> print full history\\
    %dhist n     -> print last n entries only\\
    %dhist n1 n2 -> print entries between n1 and n2 (n1 not included)\\

    This history is automatically maintained by the %cd command, and
    always available as the global list variable _dh. You can use %cd -<n>
    to go to directory number <n>."""

    dh = self.shell.user_ns['_dh']
    if parameter_s:
        try:
            args = map(int,parameter_s.split())
        except:
            self.arg_err(Magic.magic_dhist)
            return
        if len(args) == 1:
            ini,fin = max(len(dh)-(args[0]),0),len(dh)
        elif len(args) == 2:
            ini,fin = args
        else:
            self.arg_err(Magic.magic_dhist)
            return
    else:
        ini,fin = 0,len(dh)
    nlprint(dh,
            header = 'Directory history (kept in _dh)',
            start=ini,stop=fin)

ip.expose_magic("dhist", magic_dhist)

# Exit
def magic_Quit(self, parameter_s=''):
    """Exit IPython without confirmation (like %Exit)."""

    self.shell.exit_now = True
    
ip.expose_magic("Quit", magic_Quit)


# make it autocallable fn if you really need it
def magic_p(self, parameter_s=''):
    """Just a short alias for Python's 'print'."""
    exec 'print ' + parameter_s in self.shell.user_ns

ip.expose_magic("p", magic_p)

# up + enter. One char magic.
def magic_r(self, parameter_s=''):
    """Repeat previous input.

    If given an argument, repeats the previous command which starts with
    the same string, otherwise it just repeats the previous input.

    Shell escaped commands (with ! as first character) are not recognized
    by this system, only pure python code and magic commands.
    """

    start = parameter_s.strip()
    esc_magic = self.shell.ESC_MAGIC
    # Identify magic commands even if automagic is on (which means
    # the in-memory version is different from that typed by the user).
    if self.shell.rc.automagic:
        start_magic = esc_magic+start
    else:
        start_magic = start
    # Look through the input history in reverse
    for n in range(len(self.shell.input_hist)-2,0,-1):
        input = self.shell.input_hist[n]
        # skip plain 'r' lines so we don't recurse to infinity
        if input != '_ip.magic("r")\n' and \
               (input.startswith(start) or input.startswith(start_magic)):
            #print 'match',`input`  # dbg
            print 'Executing:',input,
            self.shell.runlines(input)
            return
    print 'No previous input matching `%s` found.' % start

ip.expose_magic("r", magic_r)


# use _ip.option.automagic

def magic_automagic(self, parameter_s = ''):
    """Make magic functions callable without having to type the initial %.
    
    Without argumentsl toggles on/off (when off, you must call it as
    %automagic, of course).  With arguments it sets the value, and you can
    use any of (case insensitive):

     - on,1,True: to activate
     
     - off,0,False: to deactivate.

    Note that magic functions have lowest priority, so if there's a
    variable whose name collides with that of a magic fn, automagic won't
    work for that function (you get the variable instead). However, if you
    delete the variable (del var), the previously shadowed magic function
    becomes visible to automagic again."""

    rc = self.shell.rc
    arg = parameter_s.lower()
    if parameter_s in ('on','1','true'):
        rc.automagic = True
    elif parameter_s in ('off','0','false'):
        rc.automagic = False
    else:
        rc.automagic = not rc.automagic
    print '\n' + Magic.auto_status[rc.automagic]

ip.expose_magic("automagic", magic_automagic)

# use _ip.options.autocall
def magic_autocall(self, parameter_s = ''):
    """Make functions callable without having to type parentheses.

    Usage:

       %autocall [mode]

    The mode can be one of: 0->Off, 1->Smart, 2->Full.  If not given, the
    value is toggled on and off (remembering the previous state)."""
    
    rc = self.shell.rc

    if parameter_s:
        arg = int(parameter_s)
    else:
        arg = 'toggle'

    if not arg in (0,1,2,'toggle'):
        error('Valid modes: (0->Off, 1->Smart, 2->Full')
        return

    if arg in (0,1,2):
        rc.autocall = arg
    else: # toggle
        if rc.autocall:
            self._magic_state.autocall_save = rc.autocall
            rc.autocall = 0
        else:
            try:
                rc.autocall = self._magic_state.autocall_save
            except AttributeError:
                rc.autocall = self._magic_state.autocall_save = 1
            
    print "Automatic calling is:",['OFF','Smart','Full'][rc.autocall]

ip.expose_magic("autocall", magic_autocall)