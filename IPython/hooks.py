"""hooks for IPython.

In Python, it is possible to overwrite any method of any object if you really
want to.  But IPython exposes a few 'hooks', methods which are _designed_ to
be overwritten by users for customization purposes.  This module defines the
default versions of all such hooks, which get used by IPython if not
overridden by the user.

hooks are simple functions, but they should be declared with 'self' as their
first argument, because when activated they are registered into IPython as
instance methods.  The self argument will be the IPython running instance
itself, so hooks have full access to the entire IPython object.

If you wish to define a new hook and activate it, you need to put the
necessary code into a python file which can be either imported or execfile()'d
from within your ipythonrc configuration.

For example, suppose that you have a module called 'myiphooks' in your
PYTHONPATH, which contains the following definition:

import os
import IPython.ipapi
ip = IPython.ipapi.get()

def calljed(self,filename, linenum):
    "My editor hook calls the jed editor directly."
    print "Calling my own editor, jed ..."
    os.system('jed +%d %s' % (linenum,filename))

ip.set_hook('editor', calljed)

You can then enable the functionality by doing 'import myiphooks'
somewhere in your configuration files or ipython command line.

$Id: hooks.py 2998 2008-01-31 10:06:04Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2005 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
from IPython import ipapi
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license
__version__ = Release.version

import os,bisect
from genutils import Term,shell
from pprint import PrettyPrinter

# List here all the default hooks.  For now it's just the editor functions
# but over time we'll move here all the public API for user-accessible things.
# vds: >>
__all__ = ['editor', 'fix_error_editor', 'synchronize_with_editor', 'result_display',
           'input_prefilter', 'shutdown_hook', 'late_startup_hook',
           'generate_prompt', 'generate_output_prompt','shell_hook',
           'show_in_pager','pre_prompt_hook', 'pre_runcode_hook']
# vds: <<

pformat = PrettyPrinter().pformat

def editor(self,filename, linenum=None):
    """Open the default editor at the given filename and linenumber.

    This is IPython's default editor hook, you can use it as an example to
    write your own modified one.  To set your own editor function as the
    new editor hook, call ip.set_hook('editor',yourfunc)."""

    # IPython configures a default editor at startup by reading $EDITOR from
    # the environment, and falling back on vi (unix) or notepad (win32).
    editor = self.rc.editor
    
    # marker for at which line to open the file (for existing objects)
    if linenum is None or editor=='notepad':
        linemark = ''
    else:
        linemark = '+%d' % int(linenum)
    
    # Enclose in quotes if necessary and legal
    if ' ' in editor and os.path.isfile(editor) and editor[0] != '"':
        editor = '"%s"' % editor
        
    # Call the actual editor
    os.system('%s %s %s' % (editor,linemark,filename))

import tempfile
def fix_error_editor(self,filename,linenum,column,msg):
    """Open the editor at the given filename, linenumber, column and 
    show an error message. This is used for correcting syntax errors.
    The current implementation only has special support for the VIM editor,
    and falls back on the 'editor' hook if VIM is not used.

    Call ip.set_hook('fix_error_editor',youfunc) to use your own function,
    """
    def vim_quickfix_file():
        t = tempfile.NamedTemporaryFile()
        t.write('%s:%d:%d:%s\n' % (filename,linenum,column,msg))
        t.flush()
        return t
    if os.path.basename(self.rc.editor) != 'vim':
        self.hooks.editor(filename,linenum)
        return
    t = vim_quickfix_file()
    try:
        os.system('vim --cmd "set errorformat=%f:%l:%c:%m" -q ' + t.name)
    finally:
        t.close()

# vds: >>
def synchronize_with_editor(self, filename, linenum, column):
	pass
# vds: <<

class CommandChainDispatcher:
    """ Dispatch calls to a chain of commands until some func can handle it
    
    Usage: instantiate, execute "add" to add commands (with optional
    priority), execute normally via f() calling mechanism.
    
    """
    def __init__(self,commands=None):
        if commands is None:
            self.chain = []
        else:
            self.chain = commands
            
            
    def __call__(self,*args, **kw):
        """ Command chain is called just like normal func. 
        
        This will call all funcs in chain with the same args as were given to this
        function, and return the result of first func that didn't raise
        TryNext """
        
        for prio,cmd in self.chain:
            #print "prio",prio,"cmd",cmd #dbg
            try:
                ret = cmd(*args, **kw)
                return ret
            except ipapi.TryNext, exc:
                if exc.args or exc.kwargs:
                    args = exc.args
                    kw = exc.kwargs
        # if no function will accept it, raise TryNext up to the caller
        raise ipapi.TryNext
                
    def __str__(self):
        return str(self.chain)
    
    def add(self, func, priority=0):
        """ Add a func to the cmd chain with given priority """
        bisect.insort(self.chain,(priority,func))

    def __iter__(self):
        """ Return all objects in chain.
        
        Handy if the objects are not callable.
        """
        return iter(self.chain)
    
def result_display(self,arg):
    """ Default display hook.
    
    Called for displaying the result to the user.
    """
    
    if self.rc.pprint:
        out = pformat(arg)
        if '\n' in out:
            # So that multi-line strings line up with the left column of
            # the screen, instead of having the output prompt mess up
            # their first line.                
            Term.cout.write('\n')
        print >>Term.cout, out
    else:
        # By default, the interactive prompt uses repr() to display results,
        # so we should honor this.  Users who'd rather use a different
        # mechanism can easily override this hook.
        print >>Term.cout, repr(arg)
    # the default display hook doesn't manipulate the value to put in history
    return None 

def input_prefilter(self,line):     
    """ Default input prefilter
    
    This returns the line as unchanged, so that the interpreter
    knows that nothing was done and proceeds with "classic" prefiltering
    (%magics, !shell commands etc.). 
    
    Note that leading whitespace is not passed to this hook. Prefilter
    can't alter indentation.
    
    """
    #print "attempt to rewrite",line #dbg
    return line

def shutdown_hook(self):
    """ default shutdown hook
    
    Typically, shotdown hooks should raise TryNext so all shutdown ops are done
    """
    
    #print "default shutdown hook ok" # dbg
    return

def late_startup_hook(self):
    """ Executed after ipython has been constructed and configured 
    
    """
    #print "default startup hook ok" # dbg

def generate_prompt(self, is_continuation):
    """ calculate and return a string with the prompt to display """
    ip = self.api
    if is_continuation:
        return str(ip.IP.outputcache.prompt2)
    return str(ip.IP.outputcache.prompt1)

def generate_output_prompt(self):
    ip = self.api
    return str(ip.IP.outputcache.prompt_out)

def shell_hook(self,cmd):
    """ Run system/shell command a'la os.system() """

    shell(cmd, header=self.rc.system_header, verbose=self.rc.system_verbose)

def show_in_pager(self,s):
    """ Run a string through pager """
    # raising TryNext here will use the default paging functionality
    raise ipapi.TryNext

def pre_prompt_hook(self):
    """ Run before displaying the next prompt
    
    Use this e.g. to display output from asynchronous operations (in order 
    to not mess up text entry)   
    """
    
    return None

def pre_runcode_hook(self):
    """ Executed before running the (prefiltered) code in IPython """
    return None
    

