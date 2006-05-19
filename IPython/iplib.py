# -*- coding: utf-8 -*-
"""
IPython -- An enhanced Interactive Python

Requires Python 2.3 or newer.

This file contains all the classes and helper functions specific to IPython.

$Id: iplib.py 1314 2006-05-19 18:24:14Z fperez $
"""

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
# Note: this code originally subclassed code.InteractiveConsole from the
# Python standard library.  Over time, all of that class has been copied
# verbatim here for modifications which could not be accomplished by
# subclassing.  At this point, there are no dependencies at all on the code
# module anymore (it is not even imported).  The Python License (sec. 2)
# allows for this, but it's always nice to acknowledge credit where credit is
# due.
#*****************************************************************************

#****************************************************************************
# Modules and globals

from IPython import Release
__author__  = '%s <%s>\n%s <%s>' % \
              ( Release.authors['Janko'] + Release.authors['Fernando'] )
__license__ = Release.license
__version__ = Release.version

# Python standard modules
import __main__
import __builtin__
import StringIO
import bdb
import cPickle as pickle
import codeop
import exceptions
import glob
import inspect
import keyword
import new
import os
import pdb
import pydoc
import re
import shutil
import string
import sys
import tempfile
import traceback
import types
import pickleshare

from pprint import pprint, pformat

# IPython's own modules
import IPython
from IPython import OInspect,PyColorize,ultraTB
from IPython.ColorANSI import ColorScheme,ColorSchemeTable  # too long names
from IPython.FakeModule import FakeModule
from IPython.Itpl import Itpl,itpl,printpl,ItplNS,itplns
from IPython.Logger import Logger
from IPython.Magic import Magic
from IPython.Prompts import CachedOutput
from IPython.ipstruct import Struct
from IPython.background_jobs import BackgroundJobManager
from IPython.usage import cmd_line_usage,interactive_usage
from IPython.genutils import *
import IPython.ipapi

# Globals

# store the builtin raw_input globally, and use this always, in case user code
# overwrites it (like wx.py.PyShell does)
raw_input_original = raw_input

# compiled regexps for autoindent management
dedent_re = re.compile(r'^\s+raise|^\s+return|^\s+pass')


#****************************************************************************
# Some utility function definitions

ini_spaces_re = re.compile(r'^(\s+)')

def num_ini_spaces(strng):
    """Return the number of initial spaces in a string"""

    ini_spaces = ini_spaces_re.match(strng)
    if ini_spaces:
        return ini_spaces.end()
    else:
        return 0

def softspace(file, newvalue):
    """Copied from code.py, to remove the dependency"""

    oldvalue = 0
    try:
        oldvalue = file.softspace
    except AttributeError:
        pass
    try:
        file.softspace = newvalue
    except (AttributeError, TypeError):
        # "attribute-less object" or "read-only attributes"
        pass
    return oldvalue


#****************************************************************************
# Local use exceptions
class SpaceInInput(exceptions.Exception): pass


#****************************************************************************
# Local use classes
class Bunch: pass

class Undefined: pass

class InputList(list):
    """Class to store user input.

    It's basically a list, but slices return a string instead of a list, thus
    allowing things like (assuming 'In' is an instance):

    exec In[4:7]

    or

    exec In[5:9] + In[14] + In[21:25]"""

    def __getslice__(self,i,j):
        return ''.join(list.__getslice__(self,i,j))

class SyntaxTB(ultraTB.ListTB):
    """Extension which holds some state: the last exception value"""

    def __init__(self,color_scheme = 'NoColor'):
        ultraTB.ListTB.__init__(self,color_scheme)
        self.last_syntax_error = None

    def __call__(self, etype, value, elist):
        self.last_syntax_error = value
        ultraTB.ListTB.__call__(self,etype,value,elist)

    def clear_err_state(self):
        """Return the current error state and clear it"""
        e = self.last_syntax_error
        self.last_syntax_error = None
        return e

#****************************************************************************
# Main IPython class

# FIXME: the Magic class is a mixin for now, and will unfortunately remain so
# until a full rewrite is made.  I've cleaned all cross-class uses of
# attributes and methods, but too much user code out there relies on the
# equlity %foo == __IP.magic_foo, so I can't actually remove the mixin usage.
#
# But at least now, all the pieces have been separated and we could, in
# principle, stop using the mixin.  This will ease the transition to the
# chainsaw branch.

# For reference, the following is the list of 'self.foo' uses in the Magic
# class as of 2005-12-28.  These are names we CAN'T use in the main ipython
# class, to prevent clashes.

# ['self.__class__', 'self.__dict__', 'self._inspect', 'self._ofind',
#  'self.arg_err', 'self.extract_input', 'self.format_', 'self.lsmagic',
#  'self.magic_', 'self.options_table', 'self.parse', 'self.shell',
#  'self.value']

class InteractiveShell(object,Magic):
    """An enhanced console for Python."""

    # class attribute to indicate whether the class supports threads or not.
    # Subclasses with thread support should override this as needed.
    isthreaded = False

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None,user_global_ns=None,banner2='',
                 custom_exceptions=((),None),embedded=False):

        
        # log system
        self.logger = Logger(self,logfname='ipython_log.py',logmode='rotate')

        # some minimal strict typechecks.  For some core data structures, I
        # want actual basic python types, not just anything that looks like
        # one.  This is especially true for namespaces.
        for ns in (user_ns,user_global_ns):
            if ns is not None and type(ns) != types.DictType:
                raise TypeError,'namespace must be a dictionary'

        # Job manager (for jobs run as background threads)
        self.jobs = BackgroundJobManager()

        # Do the intuitively correct thing for quit/exit: we remove the
        # builtins if they exist, and our own magics will deal with this
        try:
            del __builtin__.exit, __builtin__.quit
        except AttributeError:
            pass

        # Store the actual shell's name
        self.name = name

        # We need to know whether the instance is meant for embedding, since
        # global/local namespaces need to be handled differently in that case
        self.embedded = embedded

        # command compiler
        self.compile = codeop.CommandCompiler()

        # User input buffer
        self.buffer = []

        # Default name given in compilation of code
        self.filename = '<ipython console>'

        # Make an empty namespace, which extension writers can rely on both
        # existing and NEVER being used by ipython itself.  This gives them a
        # convenient location for storing additional information and state
        # their extensions may require, without fear of collisions with other
        # ipython names that may develop later.
        self.meta = Struct()

        # Create the namespace where the user will operate.  user_ns is
        # normally the only one used, and it is passed to the exec calls as
        # the locals argument.  But we do carry a user_global_ns namespace
        # given as the exec 'globals' argument,  This is useful in embedding
        # situations where the ipython shell opens in a context where the
        # distinction between locals and globals is meaningful.

        # FIXME. For some strange reason, __builtins__ is showing up at user
        # level as a dict instead of a module. This is a manual fix, but I
        # should really track down where the problem is coming from. Alex
        # Schmolck reported this problem first.

        # A useful post by Alex Martelli on this topic:
        # Re: inconsistent value from __builtins__
        # Von: Alex Martelli <aleaxit@yahoo.com>
        # Datum: Freitag 01 Oktober 2004 04:45:34 nachmittags/abends
        # Gruppen: comp.lang.python

        # Michael Hohn <hohn@hooknose.lbl.gov> wrote:
        # > >>> print type(builtin_check.get_global_binding('__builtins__'))
        # > <type 'dict'>
        # > >>> print type(__builtins__)
        # > <type 'module'>
        # > Is this difference in return value intentional?

        # Well, it's documented that '__builtins__' can be either a dictionary
        # or a module, and it's been that way for a long time. Whether it's
        # intentional (or sensible), I don't know. In any case, the idea is
        # that if you need to access the built-in namespace directly, you
        # should start with "import __builtin__" (note, no 's') which will
        # definitely give you a module. Yeah, it's somewhat confusing:-(.
        
        if user_ns is None:
            # Set __name__ to __main__ to better match the behavior of the
            # normal interpreter.
            user_ns = {'__name__'     :'__main__',
                       '__builtins__' : __builtin__,
                       }
            
        if user_global_ns is None:
            user_global_ns = {}

        # Assign namespaces
        # This is the namespace where all normal user variables live
        self.user_ns = user_ns
        # Embedded instances require a separate namespace for globals.
        # Normally this one is unused by non-embedded instances.
        self.user_global_ns = user_global_ns
        # A namespace to keep track of internal data structures to prevent
        # them from cluttering user-visible stuff.  Will be updated later
        self.internal_ns = {}

        # Namespace of system aliases.  Each entry in the alias
        # table must be a 2-tuple of the form (N,name), where N is the number
        # of positional arguments of the alias.
        self.alias_table = {}

        # A table holding all the namespaces IPython deals with, so that
        # introspection facilities can search easily.
        self.ns_table = {'user':user_ns,
                         'user_global':user_global_ns,
                         'alias':self.alias_table,
                         'internal':self.internal_ns,
                         'builtin':__builtin__.__dict__
                         }

        # The user namespace MUST have a pointer to the shell itself.
        self.user_ns[name] = self

        # We need to insert into sys.modules something that looks like a
        # module but which accesses the IPython namespace, for shelve and
        # pickle to work interactively. Normally they rely on getting
        # everything out of __main__, but for embedding purposes each IPython
        # instance has its own private namespace, so we can't go shoving
        # everything into __main__.

        # note, however, that we should only do this for non-embedded
        # ipythons, which really mimic the __main__.__dict__ with their own
        # namespace.  Embedded instances, on the other hand, should not do
        # this because they need to manage the user local/global namespaces
        # only, but they live within a 'normal' __main__ (meaning, they
        # shouldn't overtake the execution environment of the script they're
        # embedded in).

        if not embedded:
            try:
                main_name = self.user_ns['__name__']
            except KeyError:
                raise KeyError,'user_ns dictionary MUST have a "__name__" key'
            else:
                #print "pickle hack in place"  # dbg
                #print 'main_name:',main_name # dbg
                sys.modules[main_name] = FakeModule(self.user_ns)

        # List of input with multi-line handling.
        # Fill its zero entry, user counter starts at 1
        self.input_hist = InputList(['\n'])
        # This one will hold the 'raw' input history, without any
        # pre-processing.  This will allow users to retrieve the input just as
        # it was exactly typed in by the user, with %hist -r.
        self.input_hist_raw = InputList(['\n'])

        # list of visited directories
        try:
            self.dir_hist = [os.getcwd()]
        except IOError, e:
            self.dir_hist = []

        # dict of output history
        self.output_hist = {}

        # dict of things NOT to alias (keywords, builtins and some magics)
        no_alias = {}
        no_alias_magics = ['cd','popd','pushd','dhist','alias','unalias']
        for key in keyword.kwlist + no_alias_magics:
            no_alias[key] = 1
        no_alias.update(__builtin__.__dict__)
        self.no_alias = no_alias
                
        # make global variables for user access to these
        self.user_ns['_ih'] = self.input_hist
        self.user_ns['_oh'] = self.output_hist
        self.user_ns['_dh'] = self.dir_hist

        # user aliases to input and output histories
        self.user_ns['In']  = self.input_hist
        self.user_ns['Out'] = self.output_hist

        # Object variable to store code object waiting execution.  This is
        # used mainly by the multithreaded shells, but it can come in handy in
        # other situations.  No need to use a Queue here, since it's a single
        # item which gets cleared once run.
        self.code_to_run = None
        
        # escapes for automatic behavior on the command line
        self.ESC_SHELL  = '!'
        self.ESC_HELP   = '?'
        self.ESC_MAGIC  = '%'
        self.ESC_QUOTE  = ','
        self.ESC_QUOTE2 = ';'
        self.ESC_PAREN  = '/'

        # And their associated handlers
        self.esc_handlers = {self.ESC_PAREN  : self.handle_auto,
                             self.ESC_QUOTE  : self.handle_auto,
                             self.ESC_QUOTE2 : self.handle_auto,
                             self.ESC_MAGIC  : self.handle_magic,
                             self.ESC_HELP   : self.handle_help,
                             self.ESC_SHELL  : self.handle_shell_escape,
                             }

        # class initializations
        Magic.__init__(self,self)

        # Python source parser/formatter for syntax highlighting
        pyformat = PyColorize.Parser().format
        self.pycolorize = lambda src: pyformat(src,'str',self.rc['colors'])

        # hooks holds pointers used for user-side customizations
        self.hooks = Struct()
        
        # Set all default hooks, defined in the IPython.hooks module.
        hooks = IPython.hooks
        for hook_name in hooks.__all__:
            # default hooks have priority 100, i.e. low; user hooks should have 0-100 priority
            self.set_hook(hook_name,getattr(hooks,hook_name), 100)
            #print "bound hook",hook_name

        # Flag to mark unconditional exit
        self.exit_now = False

        self.usage_min =  """\
        An enhanced console for Python.
        Some of its features are:
        - Readline support if the readline library is present.
        - Tab completion in the local namespace.
        - Logging of input, see command-line options.
        - System shell escape via ! , eg !ls.
        - Magic commands, starting with a % (like %ls, %pwd, %cd, etc.)
        - Keeps track of locally defined variables via %who, %whos.
        - Show object information with a ? eg ?x or x? (use ?? for more info).
        """
        if usage: self.usage = usage
        else: self.usage = self.usage_min

        # Storage
        self.rc = rc   # This will hold all configuration information
        self.pager = 'less'
        # temporary files used for various purposes.  Deleted at exit.
        self.tempfiles = []

        # Keep track of readline usage (later set by init_readline)
        self.has_readline = False

        # template for logfile headers.  It gets resolved at runtime by the
        # logstart method.
        self.loghead_tpl = \
"""#log# Automatic Logger file. *** THIS MUST BE THE FIRST LINE ***
#log# DO NOT CHANGE THIS LINE OR THE TWO BELOW
#log# opts = %s
#log# args = %s
#log# It is safe to make manual edits below here.
#log#-----------------------------------------------------------------------
"""
        # for pushd/popd management
        try:
            self.home_dir = get_home_dir()
        except HomeDirError,msg:
            fatal(msg)

        self.dir_stack = [os.getcwd().replace(self.home_dir,'~')]

        # Functions to call the underlying shell.

        # utility to expand user variables via Itpl
        self.var_expand = lambda cmd: str(ItplNS(cmd.replace('#','\#'),
                                                 self.user_ns))
        # The first is similar to os.system, but it doesn't return a value,
        # and it allows interpolation of variables in the user's namespace.
        self.system = lambda cmd: shell(self.var_expand(cmd),
                                        header='IPython system call: ',
                                        verbose=self.rc.system_verbose)
        # These are for getoutput and getoutputerror:
        self.getoutput = lambda cmd: \
                         getoutput(self.var_expand(cmd),
                                   header='IPython system call: ',
                                   verbose=self.rc.system_verbose)
        self.getoutputerror = lambda cmd: \
                              getoutputerror(str(ItplNS(cmd.replace('#','\#'),
                                                        self.user_ns)),
                                             header='IPython system call: ',
                                             verbose=self.rc.system_verbose)
 
        # RegExp for splitting line contents into pre-char//first
        # word-method//rest.  For clarity, each group in on one line.

        # WARNING: update the regexp if the above escapes are changed, as they
        # are hardwired in.

        # Don't get carried away with trying to make the autocalling catch too
        # much:  it's better to be conservative rather than to trigger hidden
        # evals() somewhere and end up causing side effects.

        self.line_split = re.compile(r'^([\s*,;/])'
                                     r'([\?\w\.]+\w*\s*)'
                                     r'(\(?.*$)')

        # Original re, keep around for a while in case changes break something
        #self.line_split = re.compile(r'(^[\s*!\?%,/]?)'
        #                             r'(\s*[\?\w\.]+\w*\s*)'
        #                             r'(\(?.*$)')

        # RegExp to identify potential function names
        self.re_fun_name = re.compile(r'[a-zA-Z_]([a-zA-Z0-9_.]*) *$')

        # RegExp to exclude strings with this start from autocalling.  In
        # particular, all binary operators should be excluded, so that if foo
        # is callable, foo OP bar doesn't become foo(OP bar), which is
        # invalid.  The characters '!=()' don't need to be checked for, as the
        # _prefilter routine explicitely does so, to catch direct calls and
        # rebindings of existing names.

        # Warning: the '-' HAS TO BE AT THE END of the first group, otherwise
        # it affects the rest of the group in square brackets.
        self.re_exclude_auto = re.compile(r'^[<>,&^\|\*/\+-]'
                                          '|^is |^not |^in |^and |^or ')

        # try to catch also methods for stuff in lists/tuples/dicts: off
        # (experimental). For this to work, the line_split regexp would need
        # to be modified so it wouldn't break things at '['. That line is
        # nasty enough that I shouldn't change it until I can test it _well_.
        #self.re_fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.\[\]]*) ?$')

        # keep track of where we started running (mainly for crash post-mortem)
        self.starting_dir = os.getcwd()

        # Various switches which can be set
        self.CACHELENGTH = 5000  # this is cheap, it's just text
        self.BANNER = "Python %(version)s on %(platform)s\n" % sys.__dict__
        self.banner2 = banner2

        # TraceBack handlers:

        # Syntax error handler.
        self.SyntaxTB = SyntaxTB(color_scheme='NoColor')
        
        # The interactive one is initialized with an offset, meaning we always
        # want to remove the topmost item in the traceback, which is our own
        # internal code. Valid modes: ['Plain','Context','Verbose']
        self.InteractiveTB = ultraTB.AutoFormattedTB(mode = 'Plain',
                                                     color_scheme='NoColor',
                                                     tb_offset = 1)

        # IPython itself shouldn't crash. This will produce a detailed
        # post-mortem if it does.  But we only install the crash handler for
        # non-threaded shells, the threaded ones use a normal verbose reporter
        # and lose the crash handler.  This is because exceptions in the main
        # thread (such as in GUI code) propagate directly to sys.excepthook,
        # and there's no point in printing crash dumps for every user exception.
        if self.isthreaded:
            sys.excepthook = ultraTB.FormattedTB()
        else:
            from IPython import CrashHandler
            sys.excepthook = CrashHandler.CrashHandler(self)

        # The instance will store a pointer to this, so that runtime code
        # (such as magics) can access it.  This is because during the
        # read-eval loop, it gets temporarily overwritten (to deal with GUI
        # frameworks).
        self.sys_excepthook = sys.excepthook

        # and add any custom exception handlers the user may have specified
        self.set_custom_exc(*custom_exceptions)

        # Object inspector
        self.inspector = OInspect.Inspector(OInspect.InspectColors,
                                            PyColorize.ANSICodeColors,
                                            'NoColor')
        # indentation management
        self.autoindent = False
        self.indent_current_nsp = 0

        # Make some aliases automatically
        # Prepare list of shell aliases to auto-define
        if os.name == 'posix':
            auto_alias = ('mkdir mkdir', 'rmdir rmdir',
                          'mv mv -i','rm rm -i','cp cp -i',
                          'cat cat','less less','clear clear',
                          # a better ls
                          'ls ls -F',
                          # long ls
                          'll ls -lF',
                          # color ls
                          'lc ls -F -o --color',
                          # ls normal files only
                          'lf ls -F -o --color %l | grep ^-',
                          # ls symbolic links
                          'lk ls -F -o --color %l | grep ^l',
                          # directories or links to directories,
                          'ldir ls -F -o --color %l | grep /$',
                          # things which are executable
                          'lx ls -F -o --color %l | grep ^-..x',
                          )
        elif os.name in ['nt','dos']:
            auto_alias = ('dir dir /on', 'ls dir /on',
                          'ddir dir /ad /on', 'ldir dir /ad /on',
                          'mkdir mkdir','rmdir rmdir','echo echo',
                          'ren ren','cls cls','copy copy')
        else:
            auto_alias = ()
        self.auto_alias = map(lambda s:s.split(None,1),auto_alias)
        # Call the actual (public) initializer
        self.init_auto_alias()

        # Produce a public API instance
        self.api = IPython.ipapi.IPApi(self)

        # track which builtins we add, so we can clean up later
        self.builtins_added = {}
        # This method will add the necessary builtins for operation, but
        # tracking what it did via the builtins_added dict.
        self.add_builtins()

    # end __init__

    def pre_config_initialization(self):
        """Pre-configuration init method

        This is called before the configuration files are processed to
        prepare the services the config files might need.
        
        self.rc already has reasonable default values at this point.
        """
        rc = self.rc
        
        self.db = pickleshare.PickleShareDB(rc.ipythondir + "/db")
    
    def post_config_initialization(self):
        """Post configuration init method

        This is called after the configuration files have been processed to
        'finalize' the initialization."""

        rc = self.rc
        
        # Load readline proper
        if rc.readline:
            self.init_readline()

        # local shortcut, this is used a LOT
        self.log = self.logger.log

        # Initialize cache, set in/out prompts and printing system
        self.outputcache = CachedOutput(self,
                                        rc.cache_size,
                                        rc.pprint,
                                        input_sep = rc.separate_in,
                                        output_sep = rc.separate_out,
                                        output_sep2 = rc.separate_out2,
                                        ps1 = rc.prompt_in1,
                                        ps2 = rc.prompt_in2,
                                        ps_out = rc.prompt_out,
                                        pad_left = rc.prompts_pad_left)

        # user may have over-ridden the default print hook:
        try:
            self.outputcache.__class__.display = self.hooks.display
        except AttributeError:
            pass

        # I don't like assigning globally to sys, because it means when embedding
        # instances, each embedded instance overrides the previous choice. But
        # sys.displayhook seems to be called internally by exec, so I don't see a
        # way around it.
        sys.displayhook = self.outputcache

        # Set user colors (don't do it in the constructor above so that it
        # doesn't crash if colors option is invalid)
        self.magic_colors(rc.colors)

        # Set calling of pdb on exceptions
        self.call_pdb = rc.pdb

        # Load user aliases
        for alias in rc.alias:
            self.magic_alias(alias)
        self.hooks.late_startup_hook()
        
        for batchfile in [path(arg) for arg in self.rc.args 
            if arg.lower().endswith('.ipy')]:
            if not batchfile.isfile():
                print "No such batch file:", batchfile
                continue
            self.api.runlines(batchfile.text())

    def add_builtins(self):
        """Store ipython references into the builtin namespace.

        Some parts of ipython operate via builtins injected here, which hold a
        reference to IPython itself."""

        # TODO: deprecate all except _ip; 'jobs' should be installed 
        # by an extension and the rest are under _ip, ipalias is redundant
        builtins_new  = dict(__IPYTHON__ = self,
                             ip_set_hook = self.set_hook, 
                             jobs = self.jobs,
                             ipmagic = self.ipmagic,  
                             ipalias = self.ipalias,  
                             ipsystem = self.ipsystem,
                             _ip = self.api
                             )
        for biname,bival in builtins_new.items():
            try:
                # store the orignal value so we can restore it
                self.builtins_added[biname] =  __builtin__.__dict__[biname]
            except KeyError:
                # or mark that it wasn't defined, and we'll just delete it at
                # cleanup
                self.builtins_added[biname] = Undefined
            __builtin__.__dict__[biname] = bival
            
        # Keep in the builtins a flag for when IPython is active.  We set it
        # with setdefault so that multiple nested IPythons don't clobber one
        # another.  Each will increase its value by one upon being activated,
        # which also gives us a way to determine the nesting level.
        __builtin__.__dict__.setdefault('__IPYTHON__active',0)

    def clean_builtins(self):
        """Remove any builtins which might have been added by add_builtins, or
        restore overwritten ones to their previous values."""
        for biname,bival in self.builtins_added.items():
            if bival is Undefined:
                del __builtin__.__dict__[biname]
            else:
                __builtin__.__dict__[biname] = bival
        self.builtins_added.clear()
    
    def set_hook(self,name,hook, priority = 50):
        """set_hook(name,hook) -> sets an internal IPython hook.

        IPython exposes some of its internal API as user-modifiable hooks.  By
        adding your function to one of these hooks, you can modify IPython's 
        behavior to call at runtime your own routines."""

        # At some point in the future, this should validate the hook before it
        # accepts it.  Probably at least check that the hook takes the number
        # of args it's supposed to.
        dp = getattr(self.hooks, name, None)
        if name not in IPython.hooks.__all__:
            print "Warning! Hook '%s' is not one of %s" % (name, IPython.hooks.__all__ )
        if not dp:
            dp = IPython.hooks.CommandChainDispatcher()
        
        f = new.instancemethod(hook,self,self.__class__)
        try:
            dp.add(f,priority)
        except AttributeError:
            # it was not commandchain, plain old func - replace
            dp = f

        setattr(self.hooks,name, dp)
        
        
        #setattr(self.hooks,name,new.instancemethod(hook,self,self.__class__))

    def set_custom_exc(self,exc_tuple,handler):
        """set_custom_exc(exc_tuple,handler)

        Set a custom exception handler, which will be called if any of the
        exceptions in exc_tuple occur in the mainloop (specifically, in the
        runcode() method.

        Inputs:

          - exc_tuple: a *tuple* of valid exceptions to call the defined
          handler for.  It is very important that you use a tuple, and NOT A
          LIST here, because of the way Python's except statement works.  If
          you only want to trap a single exception, use a singleton tuple:

            exc_tuple == (MyCustomException,)

          - handler: this must be defined as a function with the following
          basic interface: def my_handler(self,etype,value,tb).

          This will be made into an instance method (via new.instancemethod)
          of IPython itself, and it will be called if any of the exceptions
          listed in the exc_tuple are caught.  If the handler is None, an
          internal basic one is used, which just prints basic info.

        WARNING: by putting in your own exception handler into IPython's main
        execution loop, you run a very good chance of nasty crashes.  This
        facility should only be used if you really know what you are doing."""

        assert type(exc_tuple)==type(()) , \
               "The custom exceptions must be given AS A TUPLE."

        def dummy_handler(self,etype,value,tb):
            print '*** Simple custom exception handler ***'
            print 'Exception type :',etype
            print 'Exception value:',value
            print 'Traceback      :',tb
            print 'Source code    :','\n'.join(self.buffer)

        if handler is None: handler = dummy_handler

        self.CustomTB = new.instancemethod(handler,self,self.__class__)
        self.custom_exceptions = exc_tuple

    def set_custom_completer(self,completer,pos=0):
        """set_custom_completer(completer,pos=0)

        Adds a new custom completer function.

        The position argument (defaults to 0) is the index in the completers
        list where you want the completer to be inserted."""

        newcomp = new.instancemethod(completer,self.Completer,
                                     self.Completer.__class__)
        self.Completer.matchers.insert(pos,newcomp)

    def _get_call_pdb(self):
        return self._call_pdb

    def _set_call_pdb(self,val):

        if val not in (0,1,False,True):
            raise ValueError,'new call_pdb value must be boolean'

        # store value in instance
        self._call_pdb = val

        # notify the actual exception handlers
        self.InteractiveTB.call_pdb = val
        if self.isthreaded:
            try:
                self.sys_excepthook.call_pdb = val
            except:
                warn('Failed to activate pdb for threaded exception handler')

    call_pdb = property(_get_call_pdb,_set_call_pdb,None,
                        'Control auto-activation of pdb at exceptions')
 

    # These special functions get installed in the builtin namespace, to
    # provide programmatic (pure python) access to magics, aliases and system
    # calls.  This is important for logging, user scripting, and more.

    # We are basically exposing, via normal python functions, the three
    # mechanisms in which ipython offers special call modes (magics for
    # internal control, aliases for direct system access via pre-selected
    # names, and !cmd for calling arbitrary system commands).

    def ipmagic(self,arg_s):
        """Call a magic function by name.

        Input: a string containing the name of the magic function to call and any
        additional arguments to be passed to the magic.

        ipmagic('name -opt foo bar') is equivalent to typing at the ipython
        prompt:

        In[1]: %name -opt foo bar

        To call a magic without arguments, simply use ipmagic('name').

        This provides a proper Python function to call IPython's magics in any
        valid Python code you can type at the interpreter, including loops and
        compound statements.  It is added by IPython to the Python builtin
        namespace upon initialization."""

        args = arg_s.split(' ',1)
        magic_name = args[0]
        magic_name = magic_name.lstrip(self.ESC_MAGIC)

        try:
            magic_args = args[1]
        except IndexError:
            magic_args = ''
        fn = getattr(self,'magic_'+magic_name,None)
        if fn is None:
            error("Magic function `%s` not found." % magic_name)
        else:
            magic_args = self.var_expand(magic_args)
            return fn(magic_args)

    def ipalias(self,arg_s):
        """Call an alias by name.

        Input: a string containing the name of the alias to call and any
        additional arguments to be passed to the magic.

        ipalias('name -opt foo bar') is equivalent to typing at the ipython
        prompt:

        In[1]: name -opt foo bar

        To call an alias without arguments, simply use ipalias('name').

        This provides a proper Python function to call IPython's aliases in any
        valid Python code you can type at the interpreter, including loops and
        compound statements.  It is added by IPython to the Python builtin
        namespace upon initialization."""

        args = arg_s.split(' ',1)
        alias_name = args[0]
        try:
            alias_args = args[1]
        except IndexError:
            alias_args = ''
        if alias_name in self.alias_table:
            self.call_alias(alias_name,alias_args)
        else:
            error("Alias `%s` not found." % alias_name)

    def ipsystem(self,arg_s):
        """Make a system call, using IPython."""

        self.system(arg_s)

    def complete(self,text):
        """Return a sorted list of all possible completions on text.

        Inputs:

          - text: a string of text to be completed on.

        This is a wrapper around the completion mechanism, similar to what
        readline does at the command line when the TAB key is hit.  By
        exposing it as a method, it can be used by other non-readline
        environments (such as GUIs) for text completion.

        Simple usage example:

        In [1]: x = 'hello'

        In [2]: __IP.complete('x.l')
        Out[2]: ['x.ljust', 'x.lower', 'x.lstrip']"""
        
        complete = self.Completer.complete
        state = 0
        # use a dict so we get unique keys, since ipyhton's multiple
        # completers can return duplicates.
        comps = {}
        while True:
            newcomp = complete(text,state)
            if newcomp is None:
                break
            comps[newcomp] = 1
            state += 1
        outcomps = comps.keys()
        outcomps.sort()
        return outcomps
        
    def set_completer_frame(self, frame=None):
        if frame:
            self.Completer.namespace = frame.f_locals
            self.Completer.global_namespace = frame.f_globals
        else:
            self.Completer.namespace = self.user_ns
            self.Completer.global_namespace = self.user_global_ns

    def init_auto_alias(self):
        """Define some aliases automatically.

        These are ALL parameter-less aliases"""

        for alias,cmd in self.auto_alias:
            self.alias_table[alias] = (0,cmd)

    def alias_table_validate(self,verbose=0):
        """Update information about the alias table.

        In particular, make sure no Python keywords/builtins are in it."""

        no_alias = self.no_alias
        for k in self.alias_table.keys():
            if k in no_alias:
                del self.alias_table[k]
                if verbose:
                    print ("Deleting alias <%s>, it's a Python "
                           "keyword or builtin." % k)
    
    def set_autoindent(self,value=None):
        """Set the autoindent flag, checking for readline support.

        If called with no arguments, it acts as a toggle."""

        if not self.has_readline:
            if os.name == 'posix':
                warn("The auto-indent feature requires the readline library")
            self.autoindent = 0
            return
        if value is None:
            self.autoindent = not self.autoindent
        else:
            self.autoindent = value

    def rc_set_toggle(self,rc_field,value=None):
        """Set or toggle a field in IPython's rc config. structure.

        If called with no arguments, it acts as a toggle.

        If called with a non-existent field, the resulting AttributeError
        exception will propagate out."""

        rc_val = getattr(self.rc,rc_field)
        if value is None:
            value = not rc_val
        setattr(self.rc,rc_field,value)

    def user_setup(self,ipythondir,rc_suffix,mode='install'):
        """Install the user configuration directory.

        Can be called when running for the first time or to upgrade the user's
        .ipython/ directory with the mode parameter. Valid modes are 'install'
        and 'upgrade'."""

        def wait():
            try:
                raw_input("Please press <RETURN> to start IPython.")
            except EOFError:
                print >> Term.cout
            print '*'*70

        cwd = os.getcwd()  # remember where we started
        glb = glob.glob
        print '*'*70
        if mode == 'install':
            print \
"""Welcome to IPython. I will try to create a personal configuration directory
where you can customize many aspects of IPython's functionality in:\n"""
        else:
            print 'I am going to upgrade your configuration in:'

        print ipythondir

        rcdirend = os.path.join('IPython','UserConfig')
        cfg = lambda d: os.path.join(d,rcdirend)
        try:
            rcdir = filter(os.path.isdir,map(cfg,sys.path))[0]
        except IOError:
            warning = """
Installation error. IPython's directory was not found.

Check the following:

The ipython/IPython directory should be in a directory belonging to your
PYTHONPATH environment variable (that is, it should be in a directory
belonging to sys.path). You can copy it explicitly there or just link to it.

IPython will proceed with builtin defaults.
"""
            warn(warning)
            wait()
            return

        if mode == 'install':
            try:
                shutil.copytree(rcdir,ipythondir)
                os.chdir(ipythondir)
                rc_files = glb("ipythonrc*")
                for rc_file in rc_files:
                    os.rename(rc_file,rc_file+rc_suffix)
            except:
                warning = """

There was a problem with the installation:
%s
Try to correct it or contact the developers if you think it's a bug.
IPython will proceed with builtin defaults.""" % sys.exc_info()[1]
                warn(warning)
                wait()
                return

        elif mode == 'upgrade':
            try:
                os.chdir(ipythondir)
            except:
                print """
Can not upgrade: changing to directory %s failed. Details:
%s
""" % (ipythondir,sys.exc_info()[1])
                wait()
                return
            else:
                sources = glb(os.path.join(rcdir,'[A-Za-z]*'))
                for new_full_path in sources:
                    new_filename = os.path.basename(new_full_path)
                    if new_filename.startswith('ipythonrc'):
                        new_filename = new_filename + rc_suffix
                    # The config directory should only contain files, skip any
                    # directories which may be there (like CVS)
                    if os.path.isdir(new_full_path):
                        continue
                    if os.path.exists(new_filename):
                        old_file = new_filename+'.old'
                        if os.path.exists(old_file):
                            os.remove(old_file)
                        os.rename(new_filename,old_file)
                    shutil.copy(new_full_path,new_filename)
        else:
            raise ValueError,'unrecognized mode for install:',`mode`

        # Fix line-endings to those native to each platform in the config
        # directory.
        try:
            os.chdir(ipythondir)
        except:
            print """
Problem: changing to directory %s failed.
Details:
%s

Some configuration files may have incorrect line endings.  This should not
cause any problems during execution.  """ % (ipythondir,sys.exc_info()[1])
            wait()
        else:
            for fname in glb('ipythonrc*'):
                try:
                    native_line_ends(fname,backup=0)
                except IOError:
                    pass

        if mode == 'install':
            print """
Successful installation!

Please read the sections 'Initial Configuration' and 'Quick Tips' in the
IPython manual (there are both HTML and PDF versions supplied with the
distribution) to make sure that your system environment is properly configured
to take advantage of IPython's features.

Important note: the configuration system has changed! The old system is
still in place, but its setting may be partly overridden by the settings in 
"~/.ipython/ipy_user_conf.py" config file. Please take a look at the file 
if some of the new settings bother you. 

"""
        else:
            print """
Successful upgrade!

All files in your directory:
%(ipythondir)s
which would have been overwritten by the upgrade were backed up with a .old
extension.  If you had made particular customizations in those files you may
want to merge them back into the new files.""" % locals()
        wait()
        os.chdir(cwd)
        # end user_setup()

    def atexit_operations(self):
        """This will be executed at the time of exit.

        Saving of persistent data should be performed here. """

        #print '*** IPython exit cleanup ***' # dbg
        # input history
        self.savehist()

        # Cleanup all tempfiles left around
        for tfile in self.tempfiles:
            try:
                os.unlink(tfile)
            except OSError:
                pass

        # save the "persistent data" catch-all dictionary
        self.hooks.shutdown_hook()
        
    def savehist(self):
        """Save input history to a file (via readline library)."""
        try:
            self.readline.write_history_file(self.histfile)
        except:
            print 'Unable to save IPython command history to file: ' + \
                  `self.histfile`

    def pre_readline(self):
        """readline hook to be used at the start of each line.

        Currently it handles auto-indent only."""

        #debugx('self.indent_current_nsp','pre_readline:')
        self.readline.insert_text(self.indent_current_str())

    def init_readline(self):
        """Command history completion/saving/reloading."""

        import IPython.rlineimpl as readline
        if not readline.have_readline:
            self.has_readline = 0
            self.readline = None
            # no point in bugging windows users with this every time:
            warn('Readline services not available on this platform.')
        else:
            sys.modules['readline'] = readline
            import atexit
            from IPython.completer import IPCompleter
            self.Completer = IPCompleter(self,
                                            self.user_ns,
                                            self.user_global_ns,
                                            self.rc.readline_omit__names,
                                            self.alias_table)

            # Platform-specific configuration
            if os.name == 'nt':
                self.readline_startup_hook = readline.set_pre_input_hook
            else:
                self.readline_startup_hook = readline.set_startup_hook

            # Load user's initrc file (readline config)
            inputrc_name = os.environ.get('INPUTRC')
            if inputrc_name is None:
                home_dir = get_home_dir()
                if home_dir is not None:
                    inputrc_name = os.path.join(home_dir,'.inputrc')
            if os.path.isfile(inputrc_name):
                try:
                    readline.read_init_file(inputrc_name)
                except:
                    warn('Problems reading readline initialization file <%s>'
                         % inputrc_name)
            
            self.has_readline = 1
            self.readline = readline
            # save this in sys so embedded copies can restore it properly
            sys.ipcompleter = self.Completer.complete
            readline.set_completer(self.Completer.complete)

            # Configure readline according to user's prefs
            for rlcommand in self.rc.readline_parse_and_bind:
                readline.parse_and_bind(rlcommand)

            # remove some chars from the delimiters list
            delims = readline.get_completer_delims()
            delims = delims.translate(string._idmap,
                                      self.rc.readline_remove_delims)
            readline.set_completer_delims(delims)
            # otherwise we end up with a monster history after a while:
            readline.set_history_length(1000)
            try:
                #print '*** Reading readline history'  # dbg
                readline.read_history_file(self.histfile)
            except IOError:
                pass  # It doesn't exist yet.

            atexit.register(self.atexit_operations)
            del atexit

        # Configure auto-indent for all platforms
        self.set_autoindent(self.rc.autoindent)

    def _should_recompile(self,e):
        """Utility routine for edit_syntax_error"""

        if e.filename in ('<ipython console>','<input>','<string>',
                          '<console>',None):
                              
            return False
        try:
            if (self.rc.autoedit_syntax and 
                not ask_yes_no('Return to editor to correct syntax error? '
                              '[Y/n] ','y')):
                return False
        except EOFError:
            return False

        def int0(x):
            try:
                return int(x)
            except TypeError:
                return 0
        # always pass integer line and offset values to editor hook
        self.hooks.fix_error_editor(e.filename,
            int0(e.lineno),int0(e.offset),e.msg)
        return True
        
    def edit_syntax_error(self):
        """The bottom half of the syntax error handler called in the main loop.

        Loop until syntax error is fixed or user cancels.
        """

        while self.SyntaxTB.last_syntax_error:
            # copy and clear last_syntax_error
            err = self.SyntaxTB.clear_err_state()
            if not self._should_recompile(err):
                return
            try:
                # may set last_syntax_error again if a SyntaxError is raised
                self.safe_execfile(err.filename,self.shell.user_ns)
            except:
                self.showtraceback()
            else:
                f = file(err.filename)
                try:
                    sys.displayhook(f.read())
                finally:
                    f.close()

    def showsyntaxerror(self, filename=None):
        """Display the syntax error that just occurred.

        This doesn't display a stack trace because there isn't one.

        If a filename is given, it is stuffed in the exception instead
        of what was there before (because Python's parser always uses
        "<string>" when reading from a string).
        """
        etype, value, last_traceback = sys.exc_info()

        # See note about these variables in showtraceback() below
        sys.last_type = etype
        sys.last_value = value
        sys.last_traceback = last_traceback
        
        if filename and etype is SyntaxError:
            # Work hard to stuff the correct filename in the exception
            try:
                msg, (dummy_filename, lineno, offset, line) = value
            except:
                # Not the format we expect; leave it alone
                pass
            else:
                # Stuff in the right filename
                try:
                    # Assume SyntaxError is a class exception
                    value = SyntaxError(msg, (filename, lineno, offset, line))
                except:
                    # If that failed, assume SyntaxError is a string
                    value = msg, (filename, lineno, offset, line)
        self.SyntaxTB(etype,value,[])

    def debugger(self):
        """Call the pdb debugger."""

        if not self.rc.pdb:
            return
        pdb.pm()

    def showtraceback(self,exc_tuple = None,filename=None,tb_offset=None):
        """Display the exception that just occurred."""

        # Though this won't be called by syntax errors in the input line,
        # there may be SyntaxError cases whith imported code.
        if exc_tuple is None:
            etype, value, tb = sys.exc_info()
        else:
            etype, value, tb = exc_tuple
        if etype is SyntaxError:
            self.showsyntaxerror(filename)
        else:
            # WARNING: these variables are somewhat deprecated and not
            # necessarily safe to use in a threaded environment, but tools
            # like pdb depend on their existence, so let's set them.  If we
            # find problems in the field, we'll need to revisit their use.
            sys.last_type = etype
            sys.last_value = value
            sys.last_traceback = tb
            
            self.InteractiveTB(etype,value,tb,tb_offset=tb_offset)
            if self.InteractiveTB.call_pdb and self.has_readline:
                # pdb mucks up readline, fix it back
                self.readline.set_completer(self.Completer.complete)

    def mainloop(self,banner=None):
        """Creates the local namespace and starts the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner."""
        
        if self.rc.c:  # Emulate Python's -c option
            self.exec_init_cmd()
        if banner is None:
            if not self.rc.banner:
                banner = ''
            # banner is string? Use it directly!
            elif isinstance(self.rc.banner,basestring):
                banner = self.rc.banner
            else:                
                banner = self.BANNER+self.banner2

        self.interact(banner)

    def exec_init_cmd(self):
        """Execute a command given at the command line.

        This emulates Python's -c option."""

        #sys.argv = ['-c']
        self.push(self.rc.c)

    def embed_mainloop(self,header='',local_ns=None,global_ns=None,stack_depth=0):
        """Embeds IPython into a running python program.

        Input:

          - header: An optional header message can be specified.

          - local_ns, global_ns: working namespaces. If given as None, the
          IPython-initialized one is updated with __main__.__dict__, so that
          program variables become visible but user-specific configuration
          remains possible.

          - stack_depth: specifies how many levels in the stack to go to
          looking for namespaces (when local_ns and global_ns are None).  This
          allows an intermediate caller to make sure that this function gets
          the namespace from the intended level in the stack.  By default (0)
          it will get its locals and globals from the immediate caller.

        Warning: it's possible to use this in a program which is being run by
        IPython itself (via %run), but some funny things will happen (a few
        globals get overwritten). In the future this will be cleaned up, as
        there is no fundamental reason why it can't work perfectly."""

        # Get locals and globals from caller
        if local_ns is None or global_ns is None:
            call_frame = sys._getframe(stack_depth).f_back

            if local_ns is None:
                local_ns = call_frame.f_locals
            if global_ns is None:
                global_ns = call_frame.f_globals

        # Update namespaces and fire up interpreter

        # The global one is easy, we can just throw it in
        self.user_global_ns = global_ns

        # but the user/local one is tricky: ipython needs it to store internal
        # data, but we also need the locals.  We'll copy locals in the user
        # one, but will track what got copied so we can delete them at exit.
        # This is so that a later embedded call doesn't see locals from a
        # previous call (which most likely existed in a separate scope).
        local_varnames = local_ns.keys()
        self.user_ns.update(local_ns)

        # Patch for global embedding to make sure that things don't overwrite
        # user globals accidentally. Thanks to Richard <rxe@renre-europe.com>
        # FIXME. Test this a bit more carefully (the if.. is new)
        if local_ns is None and global_ns is None:
            self.user_global_ns.update(__main__.__dict__)

        # make sure the tab-completer has the correct frame information, so it
        # actually completes using the frame's locals/globals
        self.set_completer_frame()

        # before activating the interactive mode, we need to make sure that
        # all names in the builtin namespace needed by ipython point to
        # ourselves, and not to other instances.
        self.add_builtins()
        
        self.interact(header)
        
        # now, purge out the user namespace from anything we might have added
        # from the caller's local namespace
        delvar = self.user_ns.pop
        for var in local_varnames:
            delvar(var,None)
        # and clean builtins we may have overridden
        self.clean_builtins()

    def interact(self, banner=None):
        """Closely emulate the interactive Python console.

        The optional banner argument specify the banner to print
        before the first interaction; by default it prints a banner
        similar to the one printed by the real Python interpreter,
        followed by the current class name in parentheses (so as not
        to confuse this with the real interpreter -- since it's so
        close!).

        """
        cprt = 'Type "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write(banner)

        more = 0
        
        # Mark activity in the builtins
        __builtin__.__dict__['__IPYTHON__active'] += 1

        # exit_now is set by a call to %Exit or %Quit
        self.exit_now = False
        while not self.exit_now:
            if more:
                prompt = self.outputcache.prompt2
                if self.autoindent:
                    self.readline_startup_hook(self.pre_readline)
            else:
                prompt = self.outputcache.prompt1
            try:
                line = self.raw_input(prompt,more)
                if self.autoindent:
                    self.readline_startup_hook(None)
            except KeyboardInterrupt:
                self.write('\nKeyboardInterrupt\n')
                self.resetbuffer()
                # keep cache in sync with the prompt counter:
                self.outputcache.prompt_count -= 1

                if self.autoindent:
                    self.indent_current_nsp = 0
                more = 0
            except EOFError:
                if self.autoindent:
                    self.readline_startup_hook(None)
                self.write('\n')
                self.exit()
            except bdb.BdbQuit:
                warn('The Python debugger has exited with a BdbQuit exception.\n'
                     'Because of how pdb handles the stack, it is impossible\n'
                     'for IPython to properly format this particular exception.\n'
                     'IPython will resume normal operation.')
            except:
                # exceptions here are VERY RARE, but they can be triggered
                # asynchronously by signal handlers, for example.
                self.showtraceback()
            else:
                more = self.push(line)
                if (self.SyntaxTB.last_syntax_error and
                    self.rc.autoedit_syntax):
                    self.edit_syntax_error()
            
        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1

    def excepthook(self, etype, value, tb):
      """One more defense for GUI apps that call sys.excepthook.

      GUI frameworks like wxPython trap exceptions and call
      sys.excepthook themselves.  I guess this is a feature that
      enables them to keep running after exceptions that would
      otherwise kill their mainloop. This is a bother for IPython
      which excepts to catch all of the program exceptions with a try:
      except: statement.

      Normally, IPython sets sys.excepthook to a CrashHandler instance, so if
      any app directly invokes sys.excepthook, it will look to the user like
      IPython crashed.  In order to work around this, we can disable the
      CrashHandler and replace it with this excepthook instead, which prints a
      regular traceback using our InteractiveTB.  In this fashion, apps which
      call sys.excepthook will generate a regular-looking exception from
      IPython, and the CrashHandler will only be triggered by real IPython
      crashes.

      This hook should be used sparingly, only in places which are not likely
      to be true IPython errors.
      """
      self.showtraceback((etype,value,tb),tb_offset=0)

    def transform_alias(self, alias,rest=''):
        """ Transform alias to system command string 
        
        """
        nargs,cmd = self.alias_table[alias]
        if ' ' in cmd and os.path.isfile(cmd):
            cmd = '"%s"' % cmd

        # Expand the %l special to be the user's input line
        if cmd.find('%l') >= 0:
            cmd = cmd.replace('%l',rest)
            rest = ''
        if nargs==0:
            # Simple, argument-less aliases
            cmd = '%s %s' % (cmd,rest)
        else:
            # Handle aliases with positional arguments
            args = rest.split(None,nargs)
            if len(args)< nargs:
                error('Alias <%s> requires %s arguments, %s given.' %
                      (alias,nargs,len(args)))
                return None
            cmd = '%s %s' % (cmd % tuple(args[:nargs]),' '.join(args[nargs:]))
        # Now call the macro, evaluating in the user's namespace

        return cmd
        
    def call_alias(self,alias,rest=''):
        """Call an alias given its name and the rest of the line.

        This is only used to provide backwards compatibility for users of
        ipalias(), use of which is not recommended for anymore."""

        # Now call the macro, evaluating in the user's namespace
        cmd = self.transform_alias(alias, rest)
        try:
            self.system(cmd)
        except:
            self.showtraceback()

    def indent_current_str(self):
        """return the current level of indentation as a string"""
        return self.indent_current_nsp * ' '

    def autoindent_update(self,line):
        """Keep track of the indent level."""

        #debugx('line')
        #debugx('self.indent_current_nsp')
        if self.autoindent:
            if line:
                inisp = num_ini_spaces(line)
                if inisp < self.indent_current_nsp:
                    self.indent_current_nsp = inisp

                if line[-1] == ':':
                    self.indent_current_nsp += 4
                elif dedent_re.match(line):
                    self.indent_current_nsp -= 4
            else:
                self.indent_current_nsp = 0

    def runlines(self,lines):
        """Run a string of one or more lines of source.

        This method is capable of running a string containing multiple source
        lines, as if they had been entered at the IPython prompt.  Since it
        exposes IPython's processing machinery, the given strings can contain
        magic calls (%magic), special shell access (!cmd), etc."""

        # We must start with a clean buffer, in case this is run from an
        # interactive IPython session (via a magic, for example).
        self.resetbuffer()
        lines = lines.split('\n')
        more = 0
        for line in lines:
            # skip blank lines so we don't mess up the prompt counter, but do
            # NOT skip even a blank line if we are in a code block (more is
            # true)
            if line or more:
                more = self.push(self.prefilter(line,more))
                # IPython's runsource returns None if there was an error
                # compiling the code.  This allows us to stop processing right
                # away, so the user gets the error message at the right place.
                if more is None:
                    break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            self.push('\n')

    def runsource(self, source, filename='<input>', symbol='single'):
        """Compile and run some source in the interpreter.

        Arguments are as for compile_command().

        One several things can happen:

        1) The input is incorrect; compile_command() raised an
        exception (SyntaxError or OverflowError).  A syntax traceback
        will be printed by calling the showsyntaxerror() method.

        2) The input is incomplete, and more input is required;
        compile_command() returned None.  Nothing happens.

        3) The input is complete; compile_command() returned a code
        object.  The code is executed by calling self.runcode() (which
        also handles run-time exceptions, except for SystemExit).

        The return value is:

          - True in case 2

          - False in the other cases, unless an exception is raised, where
          None is returned instead.  This can be used by external callers to
          know whether to continue feeding input or not.

        The return value can be used to decide whether to use sys.ps1 or
        sys.ps2 to prompt the next line."""

        try:
            code = self.compile(source,filename,symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return None

        if code is None:
            # Case 2
            return True

        # Case 3
        # We store the code object so that threaded shells and
        # custom exception handlers can access all this info if needed.
        # The source corresponding to this can be obtained from the
        # buffer attribute as '\n'.join(self.buffer).
        self.code_to_run = code
        # now actually execute the code object
        if self.runcode(code) == 0:
            return False
        else:
            return None

    def runcode(self,code_obj):
        """Execute a code object.

        When an exception occurs, self.showtraceback() is called to display a
        traceback.

        Return value: a flag indicating whether the code to be run completed
        successfully:

          - 0: successful execution.
          - 1: an error occurred.
        """

        # Set our own excepthook in case the user code tries to call it
        # directly, so that the IPython crash handler doesn't get triggered
        old_excepthook,sys.excepthook = sys.excepthook, self.excepthook

        # we save the original sys.excepthook in the instance, in case config
        # code (such as magics) needs access to it.
        self.sys_excepthook = old_excepthook
        outflag = 1  # happens in more places, so it's easier as default
        try:
            try:
                # Embedded instances require separate global/local namespaces
                # so they can see both the surrounding (local) namespace and
                # the module-level globals when called inside another function.
                if self.embedded:
                    exec code_obj in self.user_global_ns, self.user_ns
                # Normal (non-embedded) instances should only have a single
                # namespace for user code execution, otherwise functions won't
                # see interactive top-level globals.
                else:
                    exec code_obj in self.user_ns
            finally:
                # Reset our crash handler in place
                sys.excepthook = old_excepthook
        except SystemExit:
            self.resetbuffer()
            self.showtraceback()
            warn("Type exit or quit to exit IPython "
                 "(%Exit or %Quit do so unconditionally).",level=1)
        except self.custom_exceptions:
            etype,value,tb = sys.exc_info()
            self.CustomTB(etype,value,tb)
        except:
            self.showtraceback()
        else:
            outflag = 0
            if softspace(sys.stdout, 0):
                print
        # Flush out code object which has been run (and source)
        self.code_to_run = None
        return outflag
        
    def push(self, line):
        """Push a line to the interpreter.

        The line should not have a trailing newline; it may have
        internal newlines.  The line is appended to a buffer and the
        interpreter's runsource() method is called with the
        concatenated contents of the buffer as source.  If this
        indicates that the command was executed or invalid, the buffer
        is reset; otherwise, the command is incomplete, and the buffer
        is left as it was after the line was appended.  The return
        value is 1 if more input is required, 0 if the line was dealt
        with in some way (this is the same as runsource()).
        """

        # autoindent management should be done here, and not in the
        # interactive loop, since that one is only seen by keyboard input.  We
        # need this done correctly even for code run via runlines (which uses
        # push).

        #print 'push line: <%s>' % line  # dbg
        self.autoindent_update(line)

        self.buffer.append(line)
        more = self.runsource('\n'.join(self.buffer), self.filename)
        if not more:
            self.resetbuffer()
        return more

    def resetbuffer(self):
        """Reset the input buffer."""
        self.buffer[:] = []
        
    def raw_input(self,prompt='',continue_prompt=False):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        Optional inputs:

          - prompt(''): a string to be printed to prompt the user.

          - continue_prompt(False): whether this line is the first one or a
          continuation in a sequence of inputs.
        """

        line = raw_input_original(prompt)

        # Try to be reasonably smart about not re-indenting pasted input more
        # than necessary.  We do this by trimming out the auto-indent initial
        # spaces, if the user's actual input started itself with whitespace.
        #debugx('self.buffer[-1]')

        if self.autoindent:
            if num_ini_spaces(line) > self.indent_current_nsp:
                line = line[self.indent_current_nsp:]
                self.indent_current_nsp = 0
            
        # store the unfiltered input before the user has any chance to modify
        # it.
        if line.strip():
            if continue_prompt:
                self.input_hist_raw[-1] += '%s\n' % line
            else:
                self.input_hist_raw.append('%s\n' % line)

        lineout = self.prefilter(line,continue_prompt)
        return lineout
        
    def split_user_input(self,line):
        """Split user input into pre-char, function part and rest."""

        lsplit = self.line_split.match(line)
        if lsplit is None:  # no regexp match returns None
            try:
                iFun,theRest = line.split(None,1)
            except ValueError:
                iFun,theRest = line,''
            pre = re.match('^(\s*)(.*)',line).groups()[0]
        else:
            pre,iFun,theRest = lsplit.groups()

        #print 'line:<%s>' % line # dbg
        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun.strip(),theRest) # dbg
        return pre,iFun.strip(),theRest

    def _prefilter(self, line, continue_prompt):
        """Calls different preprocessors, depending on the form of line."""

        # All handlers *must* return a value, even if it's blank ('').

        # Lines are NOT logged here. Handlers should process the line as
        # needed, update the cache AND log it (so that the input cache array
        # stays synced).

        # This function is _very_ delicate, and since it's also the one which
        # determines IPython's response to user input, it must be as efficient
        # as possible.  For this reason it has _many_ returns in it, trying
        # always to exit as quickly as it can figure out what it needs to do.

        # This function is the main responsible for maintaining IPython's
        # behavior respectful of Python's semantics.  So be _very_ careful if
        # making changes to anything here.

        #.....................................................................
        # Code begins

        #if line.startswith('%crash'): raise RuntimeError,'Crash now!'  # dbg

        # save the line away in case we crash, so the post-mortem handler can
        # record it
        self._last_input_line = line

        #print '***line: <%s>' % line # dbg
        
        # the input history needs to track even empty lines
        stripped = line.strip()
        
        if not stripped:
            if not continue_prompt:
                self.outputcache.prompt_count -= 1
            return self.handle_normal(line,continue_prompt)
            #return self.handle_normal('',continue_prompt)

        # print '***cont',continue_prompt  # dbg
        # special handlers are only allowed for single line statements
        if continue_prompt and not self.rc.multi_line_specials:
            return self.handle_normal(line,continue_prompt)


        # For the rest, we need the structure of the input
        pre,iFun,theRest = self.split_user_input(line)

        # See whether any pre-existing handler can take care of it
        
        rewritten = self.hooks.input_prefilter(stripped)
        if rewritten != stripped: # ok, some prefilter did something
            rewritten = pre + rewritten  # add indentation
            return self.handle_normal(rewritten)
            
        
        

        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg

        # First check for explicit escapes in the last/first character
        handler = None
        if line[-1] == self.ESC_HELP:
            handler = self.esc_handlers.get(line[-1])  # the ? can be at the end
        if handler is None:
            # look at the first character of iFun, NOT of line, so we skip
            # leading whitespace in multiline input
            handler = self.esc_handlers.get(iFun[0:1])
        if handler is not None:
            return handler(line,continue_prompt,pre,iFun,theRest)
        # Emacs ipython-mode tags certain input lines
        if line.endswith('# PYTHON-MODE'):
            return self.handle_emacs(line,continue_prompt)

        # Next, check if we can automatically execute this thing

        # Allow ! in multi-line statements if multi_line_specials is on:
        if continue_prompt and self.rc.multi_line_specials and \
               iFun.startswith(self.ESC_SHELL):
            return self.handle_shell_escape(line,continue_prompt,
                                            pre=pre,iFun=iFun,
                                            theRest=theRest)

        # Let's try to find if the input line is a magic fn
        oinfo = None
        if hasattr(self,'magic_'+iFun):
            # WARNING: _ofind uses getattr(), so it can consume generators and
            # cause other side effects.
            oinfo = self._ofind(iFun) # FIXME - _ofind is part of Magic
            if oinfo['ismagic']:
                # Be careful not to call magics when a variable assignment is
                # being made (ls='hi', for example)
                if self.rc.automagic and \
                       (len(theRest)==0 or theRest[0] not in '!=()<>,') and \
                       (self.rc.multi_line_specials or not continue_prompt):
                    return self.handle_magic(line,continue_prompt,
                                             pre,iFun,theRest)
                else:
                    return self.handle_normal(line,continue_prompt)

        # If the rest of the line begins with an (in)equality, assginment or
        # function call, we should not call _ofind but simply execute it.
        # This avoids spurious geattr() accesses on objects upon assignment.
        #
        # It also allows users to assign to either alias or magic names true
        # python variables (the magic/alias systems always take second seat to
        # true python code).
        if theRest and theRest[0] in '!=()':
            return self.handle_normal(line,continue_prompt)

        if oinfo is None:
            # let's try to ensure that _oinfo is ONLY called when autocall is
            # on.  Since it has inevitable potential side effects, at least
            # having autocall off should be a guarantee to the user that no
            # weird things will happen.

            if self.rc.autocall:
                oinfo = self._ofind(iFun) # FIXME - _ofind is part of Magic
            else:
                # in this case, all that's left is either an alias or
                # processing the line normally.
                if iFun in self.alias_table:
                    return self.handle_alias(line,continue_prompt,
                                             pre,iFun,theRest)
                 
                else:
                    return self.handle_normal(line,continue_prompt)
        
        if not oinfo['found']:
            return self.handle_normal(line,continue_prompt)
        else:
            #print 'pre<%s> iFun <%s> rest <%s>' % (pre,iFun,theRest) # dbg
            if oinfo['isalias']:
                return self.handle_alias(line,continue_prompt,
                                             pre,iFun,theRest)

            if (self.rc.autocall 
                 and
                   (
                   #only consider exclusion re if not "," or ";" autoquoting
                   (pre == self.ESC_QUOTE or pre == self.ESC_QUOTE2
                     or pre == self.ESC_PAREN) or 
                   (not self.re_exclude_auto.match(theRest)))
                 and 
                   self.re_fun_name.match(iFun) and 
                   callable(oinfo['obj'])) :
                #print 'going auto'  # dbg
                return self.handle_auto(line,continue_prompt,
                                        pre,iFun,theRest,oinfo['obj'])
            else:
                #print 'was callable?', callable(oinfo['obj'])  # dbg
                return self.handle_normal(line,continue_prompt)

        # If we get here, we have a normal Python line. Log and return.
        return self.handle_normal(line,continue_prompt)

    def _prefilter_dumb(self, line, continue_prompt):
        """simple prefilter function, for debugging"""
        return self.handle_normal(line,continue_prompt)

    # Set the default prefilter() function (this can be user-overridden)
    prefilter = _prefilter

    def handle_normal(self,line,continue_prompt=None,
                      pre=None,iFun=None,theRest=None):
        """Handle normal input lines. Use as a template for handlers."""

        # With autoindent on, we need some way to exit the input loop, and I
        # don't want to force the user to have to backspace all the way to
        # clear the line.  The rule will be in this case, that either two
        # lines of pure whitespace in a row, or a line of pure whitespace but
        # of a size different to the indent level, will exit the input loop.
        
        if (continue_prompt and self.autoindent and line.isspace() and
            (0 < abs(len(line) - self.indent_current_nsp) <= 2 or
             (self.buffer[-1]).isspace() )):
            line = ''

        self.log(line,continue_prompt)
        return line

    def handle_alias(self,line,continue_prompt=None,
                     pre=None,iFun=None,theRest=None):
        """Handle alias input lines. """

        # pre is needed, because it carries the leading whitespace.  Otherwise
        # aliases won't work in indented sections.
        transformed = self.transform_alias(iFun, theRest)        
        line_out = '%s_ip.system(%s)' % (pre, make_quoted_expr( transformed ))        
        self.log(line_out,continue_prompt)
        return line_out

    def handle_shell_escape(self, line, continue_prompt=None,
                            pre=None,iFun=None,theRest=None):
        """Execute the line in a shell, empty return value"""

        #print 'line in :', `line` # dbg
        # Example of a special handler. Others follow a similar pattern.
        if line.lstrip().startswith('!!'):
            # rewrite iFun/theRest to properly hold the call to %sx and
            # the actual command to be executed, so handle_magic can work
            # correctly
            theRest = '%s %s' % (iFun[2:],theRest)
            iFun = 'sx'
            return self.handle_magic('%ssx %s' % (self.ESC_MAGIC,
                                     line.lstrip()[2:]),
                                     continue_prompt,pre,iFun,theRest)
        else:
            cmd=line.lstrip().lstrip('!')
            line_out = '%s_ip.system(%s)' % (pre,make_quoted_expr(cmd))
        # update cache/log and return
        self.log(line_out,continue_prompt)
        return line_out

    def handle_magic(self, line, continue_prompt=None,
                     pre=None,iFun=None,theRest=None):
        """Execute magic functions."""


        cmd = '%s_ip.magic(%s)' % (pre,make_quoted_expr(iFun + " " + theRest))
        self.log(cmd,continue_prompt)
        #print 'in handle_magic, cmd=<%s>' % cmd  # dbg
        return cmd

    def handle_auto(self, line, continue_prompt=None,
                    pre=None,iFun=None,theRest=None,obj=None):
        """Hande lines which can be auto-executed, quoting if requested."""

        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg
        
        # This should only be active for single-line input!
        if continue_prompt:
            self.log(line,continue_prompt)
            return line

        auto_rewrite = True
        
        if pre == self.ESC_QUOTE:
            # Auto-quote splitting on whitespace
            newcmd = '%s("%s")' % (iFun,'", "'.join(theRest.split()) )
        elif pre == self.ESC_QUOTE2:
            # Auto-quote whole string
            newcmd = '%s("%s")' % (iFun,theRest)
        elif pre == self.ESC_PAREN:
            newcmd = '%s(%s)' % (iFun,",".join(theRest.split()))
        else:
            # Auto-paren.
            # We only apply it to argument-less calls if the autocall
            # parameter is set to 2.  We only need to check that autocall is <
            # 2, since this function isn't called unless it's at least 1.
            if not theRest and (self.rc.autocall < 2):
                newcmd = '%s %s' % (iFun,theRest)
                auto_rewrite = False
            else:
                if theRest.startswith('['):
                    if hasattr(obj,'__getitem__'):
                        # Don't autocall in this case: item access for an object
                        # which is BOTH callable and implements __getitem__.
                        newcmd = '%s %s' % (iFun,theRest)
                        auto_rewrite = False
                    else:
                        # if the object doesn't support [] access, go ahead and
                        # autocall
                        newcmd = '%s(%s)' % (iFun.rstrip(),theRest)
                elif theRest.endswith(';'):
                    newcmd = '%s(%s);' % (iFun.rstrip(),theRest[:-1])
                else:
                    newcmd = '%s(%s)' % (iFun.rstrip(), theRest)

        if auto_rewrite:
            print >>Term.cout, self.outputcache.prompt1.auto_rewrite() + newcmd
        # log what is now valid Python, not the actual user input (without the
        # final newline)
        self.log(newcmd,continue_prompt)
        return newcmd

    def handle_help(self, line, continue_prompt=None,
                    pre=None,iFun=None,theRest=None):
        """Try to get some help for the object.

        obj? or ?obj   -> basic information.
        obj?? or ??obj -> more details.
        """

        # We need to make sure that we don't process lines which would be
        # otherwise valid python, such as "x=1 # what?"
        try:
            codeop.compile_command(line)
        except SyntaxError:
            # We should only handle as help stuff which is NOT valid syntax
            if line[0]==self.ESC_HELP:
                line = line[1:]
            elif line[-1]==self.ESC_HELP:
                line = line[:-1]
            self.log('#?'+line)
            if line:
                self.magic_pinfo(line)
            else:
                page(self.usage,screen_lines=self.rc.screen_length)
            return '' # Empty string is needed here!
        except:
            # Pass any other exceptions through to the normal handler
            return self.handle_normal(line,continue_prompt)
        else:
            # If the code compiles ok, we should handle it normally
            return self.handle_normal(line,continue_prompt)

    def getapi(self):
        """ Get an IPApi object for this shell instance
        
        Getting an IPApi object is always preferable to accessing the shell
        directly, but this holds true especially for extensions.
        
        It should always be possible to implement an extension with IPApi
        alone. If not, contact maintainer to request an addition.
        
        """
        return self.api
    
    def handle_emacs(self,line,continue_prompt=None,
                    pre=None,iFun=None,theRest=None):
        """Handle input lines marked by python-mode."""

        # Currently, nothing is done.  Later more functionality can be added
        # here if needed.

        # The input cache shouldn't be updated

        return line

    def mktempfile(self,data=None):
        """Make a new tempfile and return its filename.

        This makes a call to tempfile.mktemp, but it registers the created
        filename internally so ipython cleans it up at exit time.

        Optional inputs:

          - data(None): if data is given, it gets written out to the temp file
          immediately, and the file is closed again."""

        filename = tempfile.mktemp('.py','ipython_edit_')
        self.tempfiles.append(filename)
        
        if data:
            tmp_file = open(filename,'w')
            tmp_file.write(data)
            tmp_file.close()
        return filename

    def write(self,data):
        """Write a string to the default output"""
        Term.cout.write(data)

    def write_err(self,data):
        """Write a string to the default error output"""
        Term.cerr.write(data)

    def exit(self):
        """Handle interactive exit.

        This method sets the exit_now attribute."""

        if self.rc.confirm_exit:
            if ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                self.exit_now = True
        else:
            self.exit_now = True
        return self.exit_now

    def safe_execfile(self,fname,*where,**kw):
        fname = os.path.expanduser(fname)

        # find things also in current directory
        dname = os.path.dirname(fname)
        if not sys.path.count(dname):
            sys.path.append(dname)

        try:
            xfile = open(fname)
        except:
            print >> Term.cerr, \
                  'Could not open file <%s> for safe execution.' % fname
            return None

        kw.setdefault('islog',0)
        kw.setdefault('quiet',1)
        kw.setdefault('exit_ignore',0)
        first = xfile.readline()
        loghead = str(self.loghead_tpl).split('\n',1)[0].strip()
        xfile.close()
        # line by line execution
        if first.startswith(loghead) or kw['islog']:
            print 'Loading log file <%s> one line at a time...' % fname
            if kw['quiet']:
                stdout_save = sys.stdout
                sys.stdout = StringIO.StringIO()
            try:
                globs,locs = where[0:2]
            except:
                try:
                    globs = locs = where[0]
                except:
                    globs = locs = globals()
            badblocks = []

            # we also need to identify indented blocks of code when replaying
            # logs and put them together before passing them to an exec
            # statement. This takes a bit of regexp and look-ahead work in the
            # file. It's easiest if we swallow the whole thing in memory
            # first, and manually walk through the lines list moving the
            # counter ourselves.
            indent_re = re.compile('\s+\S')
            xfile = open(fname)
            filelines = xfile.readlines()
            xfile.close()
            nlines = len(filelines)
            lnum = 0
            while lnum < nlines:
                line = filelines[lnum]
                lnum += 1
                # don't re-insert logger status info into cache
                if line.startswith('#log#'):
                    continue
                else:
                    # build a block of code (maybe a single line) for execution
                    block = line
                    try:
                        next = filelines[lnum] # lnum has already incremented
                    except:
                        next = None
                    while next and indent_re.match(next):
                        block += next
                        lnum += 1
                        try:
                            next = filelines[lnum]
                        except:
                            next = None
                    # now execute the block of one or more lines
                    try:
                        exec block in globs,locs
                    except SystemExit:
                        pass
                    except:
                        badblocks.append(block.rstrip())
            if kw['quiet']:  # restore stdout
                sys.stdout.close()
                sys.stdout = stdout_save
            print 'Finished replaying log file <%s>' % fname
            if badblocks:
                print >> sys.stderr, ('\nThe following lines/blocks in file '
                                      '<%s> reported errors:' % fname)
                    
                for badline in badblocks:
                    print >> sys.stderr, badline
        else:  # regular file execution
            try:
                execfile(fname,*where)
            except SyntaxError:
                self.showsyntaxerror()
                warn('Failure executing file: <%s>' % fname)
            except SystemExit,status:
                if not kw['exit_ignore']:
                    self.showtraceback()
                    warn('Failure executing file: <%s>' % fname)
            except:
                self.showtraceback()
                warn('Failure executing file: <%s>' % fname)

#************************* end of file <iplib.py> *****************************
