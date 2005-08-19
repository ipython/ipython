# -*- coding: utf-8 -*-
"""
IPython -- An enhanced Interactive Python

Requires Python 2.1 or newer.

This file contains all the classes and helper functions specific to IPython.

$Id: iplib.py 723 2005-08-19 17:37:46Z fperez $
"""

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
# Note: this code originally subclassed code.InteractiveConsole from the
# Python standard library.  Over time, much of that class has been copied
# verbatim here for modifications which could not be accomplished by
# subclassing.  The Python License (sec. 2) allows for this, but it's always
# nice to acknowledge credit where credit is due.
#*****************************************************************************

#****************************************************************************
# Modules and globals

from __future__ import generators  # for 2.2 backwards-compatibility

from IPython import Release
__author__  = '%s <%s>\n%s <%s>' % \
              ( Release.authors['Janko'] + Release.authors['Fernando'] )
__license__ = Release.license
__version__ = Release.version

# Python standard modules
import __main__
import __builtin__
import exceptions
import keyword
import new
import os, sys, shutil
import code, glob, types, re
import string, StringIO
import inspect, pydoc
import bdb, pdb
import UserList # don't subclass list so this works with Python2.1
from pprint import pprint, pformat
import cPickle as pickle
import traceback

# IPython's own modules
import IPython
from IPython import OInspect,PyColorize,ultraTB
from IPython.ultraTB import ColorScheme,ColorSchemeTable  # too long names
from IPython.Logger import Logger
from IPython.Magic import Magic,magic2python,shlex_split
from IPython.usage import cmd_line_usage,interactive_usage
from IPython.Struct import Struct
from IPython.Itpl import Itpl,itpl,printpl,ItplNS,itplns
from IPython.FakeModule import FakeModule
from IPython.background_jobs import BackgroundJobManager
from IPython.genutils import *

# Global pointer to the running 

# store the builtin raw_input globally, and use this always, in case user code
# overwrites it (like wx.py.PyShell does)
raw_input_original = raw_input

#****************************************************************************
# Some utility function definitions

class Bunch: pass

def esc_quotes(strng):
    """Return the input string with single and double quotes escaped out"""

    return strng.replace('"','\\"').replace("'","\\'")

def import_fail_info(mod_name,fns=None):
    """Inform load failure for a module."""

    if fns == None:
        warn("Loading of %s failed.\n" % (mod_name,))
    else:
        warn("Loading of %s from %s failed.\n" % (fns,mod_name))

def qw_lol(indata):
    """qw_lol('a b') -> [['a','b']],
    otherwise it's just a call to qw().

    We need this to make sure the modules_some keys *always* end up as a
    list of lists."""

    if type(indata) in StringTypes:
        return [qw(indata)]
    else:
        return qw(indata)

def ipmagic(arg_s):
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
    if magic_name.startswith(__IPYTHON__.ESC_MAGIC):
        magic_name = magic_name[1:]
    try:
        magic_args = args[1]
    except IndexError:
        magic_args = ''
    fn = getattr(__IPYTHON__,'magic_'+magic_name,None)
    if fn is None:
        error("Magic function `%s` not found." % magic_name)
    else:
        magic_args = __IPYTHON__.var_expand(magic_args)
        return fn(magic_args)

def ipalias(arg_s):
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
    if alias_name in __IPYTHON__.alias_table:
        __IPYTHON__.call_alias(alias_name,alias_args)
    else:
        error("Alias `%s` not found." % alias_name)

#-----------------------------------------------------------------------------
# Local use classes
try:
    from IPython import FlexCompleter

    class MagicCompleter(FlexCompleter.Completer):
        """Extension of the completer class to work on %-prefixed lines."""

        def __init__(self,shell,namespace=None,omit__names=0,alias_table=None):
            """MagicCompleter() -> completer

            Return a completer object suitable for use by the readline library
            via readline.set_completer().

            Inputs:

            - shell: a pointer to the ipython shell itself.  This is needed
            because this completer knows about magic functions, and those can
            only be accessed via the ipython instance.

            - namespace: an optional dict where completions are performed.
            
            - The optional omit__names parameter sets the completer to omit the
            'magic' names (__magicname__) for python objects unless the text
            to be completed explicitly starts with one or more underscores.

            - If alias_table is supplied, it should be a dictionary of aliases
            to complete. """

            FlexCompleter.Completer.__init__(self,namespace)
            self.magic_prefix = shell.name+'.magic_'
            self.magic_escape = shell.ESC_MAGIC
            self.readline = FlexCompleter.readline
            delims = self.readline.get_completer_delims()
            delims = delims.replace(self.magic_escape,'')
            self.readline.set_completer_delims(delims)
            self.get_line_buffer = self.readline.get_line_buffer
            self.omit__names = omit__names
            self.merge_completions = shell.rc.readline_merge_completions
            
            if alias_table is None:
                alias_table = {}
            self.alias_table = alias_table
            # Regexp to split filenames with spaces in them
            self.space_name_re = re.compile(r'([^\\] )')
            # Hold a local ref. to glob.glob for speed
            self.glob = glob.glob
            # Special handling of backslashes needed in win32 platforms
            if sys.platform == "win32":
                self.clean_glob = self._clean_glob_win32
            else:
                self.clean_glob = self._clean_glob
            self.matchers = [self.python_matches,
                             self.file_matches,
                             self.alias_matches,
                             self.python_func_kw_matches]

        # Code contributed by Alex Schmolck, for ipython/emacs integration
        def all_completions(self, text):
            """Return all possible completions for the benefit of emacs."""
            
            completions = []
            try:
                for i in xrange(sys.maxint):
                    res = self.complete(text, i)

                    if not res: break

                    completions.append(res)
            #XXX workaround for ``notDefined.<tab>``
            except NameError:
                pass
            return completions
        # /end Alex Schmolck code.

        def _clean_glob(self,text):
            return self.glob("%s*" % text)
            
        def _clean_glob_win32(self,text):
            return [f.replace("\\","/")
                    for f in self.glob("%s*" % text)]            

        def file_matches(self, text):
            """Match filneames, expanding ~USER type strings.

            Most of the seemingly convoluted logic in this completer is an
            attempt to handle filenames with spaces in them.  And yet it's not
            quite perfect, because Python's readline doesn't expose all of the
            GNU readline details needed for this to be done correctly.

            For a filename with a space in it, the printed completions will be
            only the parts after what's already been typed (instead of the
            full completions, as is normally done).  I don't think with the
            current (as of Python 2.3) Python readline it's possible to do
            better."""
            
            #print 'Completer->file_matches: <%s>' % text # dbg

            # chars that require escaping with backslash - i.e. chars
            # that readline treats incorrectly as delimiters, but we
            # don't want to treat as delimiters in filename matching
            # when escaped with backslash
            
            protectables = ' ()[]{}'

            def protect_filename(s):
                return "".join([(ch in protectables and '\\' + ch or ch)
                                for ch in s])

            lbuf = self.get_line_buffer()[:self.readline.get_endidx()]
            open_quotes = 0  # track strings with open quotes
            try:
                lsplit = shlex_split(lbuf)[-1]
            except ValueError:
                # typically an unmatched ", or backslash without escaped char.
                if lbuf.count('"')==1:
                    open_quotes = 1
                    lsplit = lbuf.split('"')[-1]
                elif lbuf.count("'")==1:
                    open_quotes = 1
                    lsplit = lbuf.split("'")[-1]
                else:
                    return None
            except IndexError:
                # tab pressed on empty line
                lsplit = ""

            if lsplit != protect_filename(lsplit):
                # if protectables are found, do matching on the whole escaped
                # name
                has_protectables = 1
                text0,text = text,lsplit
            else:
                has_protectables = 0
                text = os.path.expanduser(text)
            
            if text == "":
                return [protect_filename(f) for f in self.glob("*")]

            m0 = self.clean_glob(text.replace('\\',''))
            if has_protectables:
                # If we had protectables, we need to revert our changes to the
                # beginning of filename so that we don't double-write the part
                # of the filename we have so far
                len_lsplit = len(lsplit)
                matches = [text0 + protect_filename(f[len_lsplit:]) for f in m0]
            else:
                if open_quotes:
                    # if we have a string with an open quote, we don't need to
                    # protect the names at all (and we _shouldn't_, as it
                    # would cause bugs when the filesystem call is made).
                    matches = m0
                else:
                    matches = [protect_filename(f) for f in m0]
            if len(matches) == 1 and os.path.isdir(matches[0]):
                # Takes care of links to directories also.  Use '/'
                # explicitly, even under Windows, so that name completions
                # don't end up escaped.
                matches[0] += '/'
            return matches

        def alias_matches(self, text):
            """Match internal system aliases"""
            #print 'Completer->alias_matches:',text # dbg
            text = os.path.expanduser(text)
            aliases =  self.alias_table.keys()
            if text == "":
                return aliases
            else:
                return [alias for alias in aliases if alias.startswith(text)]
            
        def python_matches(self,text):
            """Match attributes or global python names"""
            #print 'Completer->python_matches' # dbg
            if "." in text:
                try:
                    matches = self.attr_matches(text)
                    if text.endswith('.') and self.omit__names:
                        if self.omit__names == 1:
                            # true if txt is _not_ a __ name, false otherwise:
                            no__name = (lambda txt:
                                        re.match(r'.*\.__.*?__',txt) is None)
                        else:
                            # true if txt is _not_ a _ name, false otherwise:
                            no__name = (lambda txt:
                                        re.match(r'.*\._.*?',txt) is None)
                        matches = filter(no__name, matches)
                except NameError:
                    # catches <undefined attributes>.<tab>
                    matches = []
            else:
                matches = self.global_matches(text)
                # this is so completion finds magics when automagic is on:
                if matches == [] and not text.startswith(os.sep):
                    matches = self.attr_matches(self.magic_prefix+text)
            return matches

        def _default_arguments(self, obj):
            """Return the list of default arguments of obj if it is callable,
            or empty list otherwise."""
            
            if not (inspect.isfunction(obj) or inspect.ismethod(obj)):
                # for classes, check for __init__,__new__
                if inspect.isclass(obj):
                    obj = (getattr(obj,'__init__',None) or
                           getattr(obj,'__new__',None))
                # for all others, check if they are __call__able
                elif hasattr(obj, '__call__'):
                    obj = obj.__call__
                # XXX: is there a way to handle the builtins ?
            try:
                args,_,_1,defaults = inspect.getargspec(obj)
                if defaults:
                    return args[-len(defaults):]
            except TypeError: pass
            return []

        def python_func_kw_matches(self,text):
            """Match named parameters (kwargs) of the last open function"""

            if "." in text: # a parameter cannot be dotted
                return []
            try: regexp = self.__funcParamsRegex
            except AttributeError:
                regexp = self.__funcParamsRegex = re.compile(r'''
                    '.*?' |    # single quoted strings or
                    ".*?" |    # double quoted strings or
                    \w+   |    # identifier
                    \S         # other characters
                    ''', re.VERBOSE | re.DOTALL)
            # 1. find the nearest identifier that comes before an unclosed
            # parenthesis e.g. for "foo (1+bar(x), pa", the candidate is "foo"
            tokens = regexp.findall(self.get_line_buffer())
            tokens.reverse()
            iterTokens = iter(tokens); openPar = 0
            for token in iterTokens:
                if token == ')':
                    openPar -= 1
                elif token == '(':
                    openPar += 1
                    if openPar > 0:
                        # found the last unclosed parenthesis
                        break
            else:
                return []
            # 2. Concatenate any dotted names (e.g. "foo.bar" for "foo.bar(x, pa" )
            ids = []
            isId = re.compile(r'\w+$').match
            while True:
                try:
                    ids.append(iterTokens.next())
                    if not isId(ids[-1]):
                        ids.pop(); break
                    if not iterTokens.next() == '.':
                        break
                except StopIteration:
                    break
            # lookup the candidate callable matches either using global_matches
            # or attr_matches for dotted names
            if len(ids) == 1:
                callableMatches = self.global_matches(ids[0])
            else:
                callableMatches = self.attr_matches('.'.join(ids[::-1]))
            argMatches = []
            for callableMatch in callableMatches:
                try: namedArgs = self._default_arguments(eval(callableMatch,
                                                             self.namespace))
                except: continue
                for namedArg in namedArgs:
                    if namedArg.startswith(text):
                        argMatches.append("%s=" %namedArg)
            return argMatches

        def complete(self, text, state):
            """Return the next possible completion for 'text'.

            This is called successively with state == 0, 1, 2, ... until it
            returns None.  The completion should begin with 'text'.  """
            
            #print '\n*** COMPLETE: <%s> (%s)' % (text,state)  # dbg
            magic_escape = self.magic_escape
            magic_prefix = self.magic_prefix
            
            try:
                if text.startswith(magic_escape):
                    text = text.replace(magic_escape,magic_prefix)
                elif text.startswith('~'):
                    text = os.path.expanduser(text)
                if state == 0:
                    # Extend the list of completions with the results of each
                    # matcher, so we return results to the user from all
                    # namespaces.
                    if self.merge_completions:
                        self.matches = []
                        for matcher in self.matchers:
                            self.matches.extend(matcher(text))
                    else:
                        for matcher in self.matchers:
                            self.matches = matcher(text)
                            if self.matches:
                                break
                        
                try:
                    return self.matches[state].replace(magic_prefix,magic_escape)
                except IndexError:
                    return None
            except:
                # If completion fails, don't annoy the user.
                pass

except ImportError:
    pass  # no readline support

except KeyError:
    pass  # Windows doesn't set TERM, it doesn't matter


class InputList(UserList.UserList):
    """Class to store user input.

    It's basically a list, but slices return a string instead of a list, thus
    allowing things like (assuming 'In' is an instance):

    exec In[4:7]

    or

    exec In[5:9] + In[14] + In[21:25]"""

    def __getslice__(self,i,j):
        return ''.join(UserList.UserList.__getslice__(self,i,j))

#****************************************************************************
# Local use exceptions
class SpaceInInput(exceptions.Exception):
    pass

#****************************************************************************
# Main IPython class

class InteractiveShell(code.InteractiveConsole, Logger, Magic):
    """An enhanced console for Python."""

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None,banner2='',
                 custom_exceptions=((),None)):

        # Put a reference to self in builtins so that any form of embedded or
        # imported code can test for being inside IPython.
        __builtin__.__IPYTHON__ = self

        # And load into builtins ipmagic/ipalias as well
        __builtin__.ipmagic = ipmagic
        __builtin__.ipalias = ipalias

        # Add to __builtin__ other parts of IPython's public API
        __builtin__.ip_set_hook = self.set_hook

        # Keep in the builtins a flag for when IPython is active.  We set it
        # with setdefault so that multiple nested IPythons don't clobber one
        # another.  Each will increase its value by one upon being activated,
        # which also gives us a way to determine the nesting level.
        __builtin__.__dict__.setdefault('__IPYTHON__active',0)

        # Inform the user of ipython's fast exit magics.
        _exit = ' Use %Exit or %Quit to exit without confirmation.'
        __builtin__.exit += _exit
        __builtin__.quit += _exit

        # Create the namespace where the user will operate:

        # FIXME. For some strange reason, __builtins__ is showing up at user
        # level as a dict instead of a module. This is a manual fix, but I
        # should really track down where the problem is coming from. Alex
        # Schmolck reported this problem first.

        # A useful post by Alex Martelli on this topic:
        # Re: inconsistent value from __builtins__
        # Von: Alex Martelli <aleaxit@yahoo.com>
        # Datum: Freitag 01 Oktober 2004 04:45:34 nachmittags/abends
        # Gruppen: comp.lang.python
        # Referenzen: 1

        # Michael Hohn <hohn@hooknose.lbl.gov> wrote:
        # > >>> print type(builtin_check.get_global_binding('__builtins__'))
        # > <type 'dict'>
        # > >>> print type(__builtins__)
        # > <type 'module'>
        # > Is this difference in return value intentional?

        # Well, it's documented that '__builtins__' can be either a dictionary
        # or a module, and it's been that way for a long time. Whether it's
        # intentional (or sensible), I don't know. In any case, the idea is that
        # if you need to access the built-in namespace directly, you should start
        # with "import __builtin__" (note, no 's') which will definitely give you
        # a module. Yeah, it's somewhat confusing:-(.
        
        if user_ns is None:
            # Set __name__ to __main__ to better match the behavior of the
            # normal interpreter.
            self.user_ns = {'__name__'     :'__main__',
                            '__builtins__' : __builtin__,
                            }
        else:
            self.user_ns = user_ns

        # The user namespace MUST have a pointer to the shell itself.
        self.user_ns[name] = self

        # We need to insert into sys.modules something that looks like a
        # module but which accesses the IPython namespace, for shelve and
        # pickle to work interactively. Normally they rely on getting
        # everything out of __main__, but for embedding purposes each IPython
        # instance has its own private namespace, so we can't go shoving
        # everything into __main__.

        try:
            main_name = self.user_ns['__name__']
        except KeyError:
            raise KeyError,'user_ns dictionary MUST have a "__name__" key'
        else:
            #print "pickle hack in place"  # dbg
            sys.modules[main_name] = FakeModule(self.user_ns)

        # List of input with multi-line handling.
        # Fill its zero entry, user counter starts at 1
        self.input_hist = InputList(['\n'])

        # list of visited directories
        self.dir_hist = [os.getcwd()]

        # dict of output history
        self.output_hist = {}

        # dict of names to be treated as system aliases.  Each entry in the
        # alias table must be a 2-tuple of the form (N,name), where N is the
        # number of positional arguments of the alias.
        self.alias_table = {}

        # dict of things NOT to alias (keywords and builtins)
        self.no_alias = {}
        for key in keyword.kwlist:
            self.no_alias[key] = 1
        self.no_alias.update(__builtin__.__dict__)
        
        # make global variables for user access to these
        self.user_ns['_ih'] = self.input_hist
        self.user_ns['_oh'] = self.output_hist
        self.user_ns['_dh'] = self.dir_hist

        # user aliases to input and output histories
        self.user_ns['In']  = self.input_hist
        self.user_ns['Out'] = self.output_hist

        # Store the actual shell's name
        self.name = name

        # Object variable to store code object waiting execution.  This is
        # used mainly by the multithreaded shells, but it can come in handy in
        # other situations.  No need to use a Queue here, since it's a single
        # item which gets cleared once run.
        self.code_to_run = None
        
        # Job manager (for jobs run as background threads)
        self.jobs = BackgroundJobManager()
        # Put the job manager into builtins so it's always there.
        __builtin__.jobs = self.jobs

        # escapes for automatic behavior on the command line
        self.ESC_SHELL = '!'
        self.ESC_HELP  = '?'
        self.ESC_MAGIC = '%'
        self.ESC_QUOTE = ','
        self.ESC_QUOTE2 = ';'
        self.ESC_PAREN = '/'

        # And their associated handlers
        self.esc_handlers = {self.ESC_PAREN:self.handle_auto,
                             self.ESC_QUOTE:self.handle_auto,
                             self.ESC_QUOTE2:self.handle_auto,
                             self.ESC_MAGIC:self.handle_magic,
                             self.ESC_HELP:self.handle_help,
                             self.ESC_SHELL:self.handle_shell_escape,
                             }

        # class initializations
        code.InteractiveConsole.__init__(self,locals = self.user_ns)
        Logger.__init__(self,log_ns = self.user_ns)
        Magic.__init__(self,self)

        # an ugly hack to get a pointer to the shell, so I can start writing
        # magic code via this pointer instead of the current mixin salad.
        Magic.set_shell(self,self)

        # hooks holds pointers used for user-side customizations
        self.hooks = Struct()
        
        # Set all default hooks, defined in the IPython.hooks module.
        hooks = IPython.hooks
        for hook_name in hooks.__all__:
            self.set_hook(hook_name,getattr(hooks,hook_name))

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
        self.inputcache = []
        self._boundcache = []
        self.pager = 'less'
        # temporary files used for various purposes.  Deleted at exit.
        self.tempfiles = []

        # Keep track of readline usage (later set by init_readline)
        self.has_readline = 0

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
        # RegExp to exclude strings with this start from autocalling
        self.re_exclude_auto = re.compile('^[!=()<>,\*/\+-]|^is ')
        # try to catch also methods for stuff in lists/tuples/dicts: off
        # (experimental). For this to work, the line_split regexp would need
        # to be modified so it wouldn't break things at '['. That line is
        # nasty enough that I shouldn't change it until I can test it _well_.
        #self.re_fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.\[\]]*) ?$')

        # keep track of where we started running (mainly for crash post-mortem)
        self.starting_dir = os.getcwd()

        # Attributes for Logger mixin class, make defaults here
        self._dolog = 0
        self.LOG = ''
        self.LOGDEF = '.InteractiveShell.log'
        self.LOGMODE = 'over'
        self.LOGHEAD = Itpl(
"""#log# Automatic Logger file. *** THIS MUST BE THE FIRST LINE ***
#log# DO NOT CHANGE THIS LINE OR THE TWO BELOW
#log# opts = $self.rc.opts
#log# args = $self.rc.args
#log# It is safe to make manual edits below here.
#log#-----------------------------------------------------------------------
""")
        # Various switches which can be set
        self.CACHELENGTH = 5000  # this is cheap, it's just text
        self.BANNER = "Python %(version)s on %(platform)s\n" % sys.__dict__
        self.banner2 = banner2

        # TraceBack handlers:
        # Need two, one for syntax errors and one for other exceptions.
        self.SyntaxTB = ultraTB.ListTB(color_scheme='NoColor')
        # This one is initialized with an offset, meaning we always want to
        # remove the topmost item in the traceback, which is our own internal
        # code. Valid modes: ['Plain','Context','Verbose']
        self.InteractiveTB = ultraTB.AutoFormattedTB(mode = 'Plain',
                                                     color_scheme='NoColor',
                                                     tb_offset = 1)
        # and add any custom exception handlers the user may have specified
        self.set_custom_exc(*custom_exceptions)

        # Object inspector
        ins_colors = OInspect.InspectColors
        code_colors = PyColorize.ANSICodeColors
        self.inspector = OInspect.Inspector(ins_colors,code_colors,'NoColor')
        self.autoindent = 0

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
    # end __init__

    def set_hook(self,name,hook):
        """set_hook(name,hook) -> sets an internal IPython hook.

        IPython exposes some of its internal API as user-modifiable hooks.  By
        resetting one of these hooks, you can modify IPython's behavior to
        call at runtime your own routines."""

        # At some point in the future, this should validate the hook before it
        # accepts it.  Probably at least check that the hook takes the number
        # of args it's supposed to.
        setattr(self.hooks,name,new.instancemethod(hook,self,self.__class__))

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

    def post_config_initialization(self):
        """Post configuration init method

        This is called after the configuration files have been processed to
        'finalize' the initialization."""
        
        # dynamic data that survives through sessions
        # XXX make the filename a config option?
        persist_base = 'persist'
        if self.rc.profile:
            persist_base += '_%s' % self.rc.profile
        self.persist_fname =  os.path.join(self.rc.ipythondir,persist_base)

        try:
            self.persist = pickle.load(file(self.persist_fname))
        except:
            self.persist = {}
            
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
to take advantage of IPython's features."""
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

        # input history
        self.savehist()

        # Cleanup all tempfiles left around
        for tfile in self.tempfiles:
            try:
                os.unlink(tfile)
            except OSError:
                pass

        # save the "persistent data" catch-all dictionary
        try:
            pickle.dump(self.persist, open(self.persist_fname,"w"))
        except:
            print "*** ERROR *** persistent data saving failed."
        
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
        
        self.readline.insert_text(' '* self.readline_indent)

    def init_readline(self):
        """Command history completion/saving/reloading."""
        try:
            import readline
            self.Completer = MagicCompleter(self,
                                            self.user_ns,
                                            self.rc.readline_omit__names,
                                            self.alias_table)
        except ImportError,NameError:
            # If FlexCompleter failed to import, MagicCompleter won't be 
            # defined.  This can happen because of a problem with readline
            self.has_readline = 0
            # no point in bugging windows users with this every time:
            if os.name == 'posix':
                warn('Readline services not available on this platform.')
        else:
            import atexit

            # Platform-specific configuration
            if os.name == 'nt':
                # readline under Windows modifies the default exit behavior
                # from being Ctrl-Z/Return to the Unix Ctrl-D one.
                __builtin__.exit = __builtin__.quit = \
                     ('Use Ctrl-D (i.e. EOF) to exit. '
                      'Use %Exit or %Quit to exit without confirmation.')
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
            self.readline_indent = 0  # for auto-indenting via readline
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

    def showsyntaxerror(self, filename=None):
        """Display the syntax error that just occurred.

        This doesn't display a stack trace because there isn't one.

        If a filename is given, it is stuffed in the exception instead
        of what was there before (because Python's parser always uses
        "<string>" when reading from a string).
        """
        type, value, sys.last_traceback = sys.exc_info()
        sys.last_type = type
        sys.last_value = value
        if filename and type is SyntaxError:
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
        self.SyntaxTB(type,value,[])

    def debugger(self):
        """Call the pdb debugger."""

        if not self.rc.pdb:
            return
        pdb.pm()

    def showtraceback(self,exc_tuple = None):
        """Display the exception that just occurred."""

        # Though this won't be called by syntax errors in the input line,
        # there may be SyntaxError cases whith imported code.
        if exc_tuple is None:
            type, value, tb = sys.exc_info()
        else:
            type, value, tb = exc_tuple
        if type is SyntaxError:
            self.showsyntaxerror()
        else:
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            self.InteractiveTB()
            if self.InteractiveTB.call_pdb and self.has_readline:
                # pdb mucks up readline, fix it back
                self.readline.set_completer(self.Completer.complete)

    def update_cache(self, line):
        """puts line into cache"""
        self.inputcache.insert(0, line) # This copies the cache every time ... :-(
        if len(self.inputcache) >= self.CACHELENGTH:
            self.inputcache.pop()    # This not :-)

    def name_space_init(self):
        """Create local namespace."""
        # We want this to be a method to facilitate embedded initialization.
        code.InteractiveConsole.__init__(self,self.user_ns)

    def mainloop(self,banner=None):
        """Creates the local namespace and starts the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner."""
        
        self.name_space_init()
        if self.rc.c:  # Emulate Python's -c option
            self.exec_init_cmd()
        if banner is None:
            if self.rc.banner:
                banner = self.BANNER+self.banner2
            else:
                banner = ''
        self.interact(banner)

    def exec_init_cmd(self):
        """Execute a command given at the command line.

        This emulates Python's -c option."""

        sys.argv = ['-c']
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

        # Patch for global embedding to make sure that things don't overwrite
        # user globals accidentally. Thanks to Richard <rxe@renre-europe.com>
        # FIXME. Test this a bit more carefully (the if.. is new)
        if local_ns is None and global_ns is None:
            self.user_ns.update(__main__.__dict__)

        # Get locals and globals from caller
        if local_ns is None or global_ns is None:
            call_frame = sys._getframe(stack_depth).f_back

            if local_ns is None:
                local_ns = call_frame.f_locals
            if global_ns is None:
                global_ns = call_frame.f_globals

        # Update namespaces and fire up interpreter
        self.user_ns.update(local_ns)
        self.interact(header)

        # Remove locals from namespace
        for k in local_ns:
            del self.user_ns[k]

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
        while not self.exit_now:
            try:
                if more:
                    prompt = self.outputcache.prompt2
                    if self.autoindent:
                        self.readline_startup_hook(self.pre_readline)
                else:
                    prompt = self.outputcache.prompt1
                try:
                    line = self.raw_input(prompt)
                    if self.autoindent:
                        self.readline_startup_hook(None)
                except EOFError:
                    if self.autoindent:
                        self.readline_startup_hook(None)
                    self.write("\n")
                    if self.rc.confirm_exit:
                        if ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                            break
                    else:
                        break
                else:
                    more = self.push(line)
                    # Auto-indent management
                    if self.autoindent:
                        if line:
                            ini_spaces = re.match('^(\s+)',line)
                            if ini_spaces:
                                nspaces = ini_spaces.end()
                            else:
                                nspaces = 0
                            self.readline_indent = nspaces

                            if line[-1] == ':':
                                self.readline_indent += 4
                            elif re.match(r'^\s+raise|^\s+return',line):
                                self.readline_indent -= 4
                        else:
                            self.readline_indent = 0

            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0
                # keep cache in sync with the prompt counter:
                self.outputcache.prompt_count -= 1

                if self.autoindent:
                    self.readline_indent = 0

            except bdb.BdbQuit:
                warn("The Python debugger has exited with a BdbQuit exception.\n"
                     "Because of how pdb handles the stack, it is impossible\n"
                     "for IPython to properly format this particular exception.\n"
                     "IPython will resume normal operation.")
            
        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1

    def excepthook(self, type, value, tb):
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
      
      self.InteractiveTB(type, value, tb, tb_offset=0)
      if self.InteractiveTB.call_pdb and self.has_readline:
          self.readline.set_completer(self.Completer.complete)

    def call_alias(self,alias,rest=''):
        """Call an alias given its name and the rest of the line.

        This function MUST be given a proper alias, because it doesn't make
        any checks when looking up into the alias table.  The caller is
        responsible for invoking it only with a valid alias."""

        #print 'ALIAS: <%s>+<%s>' % (alias,rest) # dbg
        nargs,cmd = self.alias_table[alias]
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
                return
            cmd = '%s %s' % (cmd % tuple(args[:nargs]),' '.join(args[nargs:]))
        # Now call the macro, evaluating in the user's namespace
        try:
            self.system(cmd)
        except:
            self.showtraceback()

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
                more = self.push((self.prefilter(line,more)))
                # IPython's runsource returns None if there was an error
                # compiling the code.  This allows us to stop processing right
                # away, so the user gets the error message at the right place.
                if more is None:
                    break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            self.push('\n')

    def runsource(self, source, filename="<input>", symbol="single"):
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
            code = self.compile(source, filename, symbol)
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
        outflag = 1  # happens in more places, so it's easier as default
        try:
            try:
                exec code_obj in self.locals
            finally:
                # Reset our crash handler in place
                sys.excepthook = old_excepthook
        except SystemExit:
            self.resetbuffer()
            self.showtraceback()
            warn( __builtin__.exit,level=1)
        except self.custom_exceptions:
            etype,value,tb = sys.exc_info()
            self.CustomTB(etype,value,tb)
        except:
            self.showtraceback()
        else:
            outflag = 0
            if code.softspace(sys.stdout, 0):
                print
        # Flush out code object which has been run (and source)
        self.code_to_run = None
        return outflag

    def raw_input(self, prompt=""):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        The base implementation uses the built-in function
        raw_input(); a subclass may replace this with a different
        implementation.
        """
        return self.prefilter(raw_input_original(prompt),
                              prompt==self.outputcache.prompt2)
        
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
        if not line.strip():
            if not continue_prompt:
                self.outputcache.prompt_count -= 1
            return self.handle_normal('',continue_prompt)

        # print '***cont',continue_prompt  # dbg
        # special handlers are only allowed for single line statements
        if continue_prompt and not self.rc.multi_line_specials:
            return self.handle_normal(line,continue_prompt)

        # For the rest, we need the structure of the input
        pre,iFun,theRest = self.split_user_input(line)
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
            oinfo = self._ofind(iFun) # FIXME - _ofind is part of Magic
        
        if not oinfo['found']:
            return self.handle_normal(line,continue_prompt)
        else:
            #print 'iFun <%s> rest <%s>' % (iFun,theRest) # dbg
            if oinfo['isalias']:
                return self.handle_alias(line,continue_prompt,
                                             pre,iFun,theRest)

            if self.rc.autocall and \
                   not self.re_exclude_auto.match(theRest) and \
                   self.re_fun_name.match(iFun) and \
                   callable(oinfo['obj']) :
                #print 'going auto'  # dbg
                return self.handle_auto(line,continue_prompt,pre,iFun,theRest)
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

        self.log(line,continue_prompt)
        self.update_cache(line)
        return line

    def handle_alias(self,line,continue_prompt=None,
                     pre=None,iFun=None,theRest=None):
        """Handle alias input lines. """

        theRest = esc_quotes(theRest)
        line_out = "%s%s.call_alias('%s','%s')" % (pre,self.name,iFun,theRest)
        self.log(line_out,continue_prompt)
        self.update_cache(line_out)
        return line_out

    def handle_shell_escape(self, line, continue_prompt=None,
                            pre=None,iFun=None,theRest=None):
        """Execute the line in a shell, empty return value"""

        #print 'line in :', `line` # dbg
        # Example of a special handler. Others follow a similar pattern.
        if continue_prompt:  # multi-line statements
            if iFun.startswith('!!'):
                print 'SyntaxError: !! is not allowed in multiline statements'
                return pre
            else:
                cmd = ("%s %s" % (iFun[1:],theRest)).replace('"','\\"')
                line_out = '%s%s.system("%s")' % (pre,self.name,cmd)
                #line_out = ('%s%s.system(' % (pre,self.name)) + repr(cmd) + ')'
        else: # single-line input
            if line.startswith('!!'):
                # rewrite iFun/theRest to properly hold the call to %sx and
                # the actual command to be executed, so handle_magic can work
                # correctly
                theRest = '%s %s' % (iFun[2:],theRest)
                iFun = 'sx'
                return self.handle_magic('%ssx %s' % (self.ESC_MAGIC,line[2:]),
                                         continue_prompt,pre,iFun,theRest)
            else:
                cmd = esc_quotes(line[1:])
                line_out = '%s.system("%s")' % (self.name,cmd)
                #line_out = ('%s.system(' % self.name) + repr(cmd)+ ')'
        # update cache/log and return
        self.log(line_out,continue_prompt)
        self.update_cache(line_out)   # readline cache gets normal line
        #print 'line out r:', `line_out` # dbg
        #print 'line out s:', line_out # dbg
        return line_out

    def handle_magic(self, line, continue_prompt=None,
                     pre=None,iFun=None,theRest=None):
        """Execute magic functions.

        Also log them with a prepended # so the log is clean Python."""

        cmd = '%sipmagic("%s")' % (pre,esc_quotes('%s %s' % (iFun,theRest)))
        self.log(cmd,continue_prompt)
        self.update_cache(line)
        #print 'in handle_magic, cmd=<%s>' % cmd  # dbg
        return cmd

    def handle_auto(self, line, continue_prompt=None,
                    pre=None,iFun=None,theRest=None):
        """Hande lines which can be auto-executed, quoting if requested."""

        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg
        
        # This should only be active for single-line input!
        if continue_prompt:
            return line

        if pre == self.ESC_QUOTE:
            # Auto-quote splitting on whitespace
            newcmd = '%s("%s")\n' % (iFun,'", "'.join(theRest.split()) )
        elif pre == self.ESC_QUOTE2:
            # Auto-quote whole string
            newcmd = '%s("%s")\n' % (iFun,theRest)
        else:
            # Auto-paren
            if theRest[0:1] in ('=','['):
                # Don't autocall in these cases.  They can be either
                # rebindings of an existing callable's name, or item access
                # for an object which is BOTH callable and implements
                # __getitem__.
                return '%s %s\n' % (iFun,theRest)
            if theRest.endswith(';'):
                newcmd = '%s(%s);\n' % (iFun.rstrip(),theRest[:-1])
            else:
                newcmd = '%s(%s)\n' % (iFun.rstrip(),theRest)

        print >>Term.cout, self.outputcache.prompt1.auto_rewrite() + newcmd,
        # log what is now valid Python, not the actual user input (without the
        # final newline)
        self.log(newcmd.strip(),continue_prompt)
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
            code.compile_command(line)
        except SyntaxError:
            # We should only handle as help stuff which is NOT valid syntax
            if line[0]==self.ESC_HELP:
                line = line[1:]
            elif line[-1]==self.ESC_HELP:
                line = line[:-1]
            self.log('#?'+line)
            self.update_cache(line)
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

    def handle_emacs(self,line,continue_prompt=None,
                    pre=None,iFun=None,theRest=None):
        """Handle input lines marked by python-mode."""

        # Currently, nothing is done.  Later more functionality can be added
        # here if needed.

        # The input cache shouldn't be updated

        return line

    def write(self,data):
        """Write a string to the default output"""
        Term.cout.write(data)

    def write_err(self,data):
        """Write a string to the default error output"""
        Term.cerr.write(data)

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
        _LOGHEAD = str(self.LOGHEAD).split('\n',1)[0].strip()
        xfile.close()
        # line by line execution
        if first.startswith(_LOGHEAD) or kw['islog']:
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
                elif line.startswith('#%s'% self.ESC_MAGIC):
                    self.update_cache(line[1:])
                    line = magic2python(line)
                elif line.startswith('#!'):
                    self.update_cache(line[1:])
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
                        self.update_cache(block.rstrip())
                    except SystemExit:
                        pass
                    except:
                        badblocks.append(block.rstrip())
            if kw['quiet']:  # restore stdout
                sys.stdout.close()
                sys.stdout = stdout_save
            print 'Finished replaying log file <%s>' % fname
            if badblocks:
                print >> sys.stderr, \
                      '\nThe following lines/blocks in file <%s> reported errors:' \
                      % fname
                for badline in badblocks:
                    print >> sys.stderr, badline
        else:  # regular file execution
            try:
                execfile(fname,*where)
            except SyntaxError:
                etype, evalue = sys.exc_info()[0:2]
                self.SyntaxTB(etype,evalue,[])
                warn('Failure executing file: <%s>' % fname)
            except SystemExit,status:
                if not kw['exit_ignore']:
                    self.InteractiveTB()
                    warn('Failure executing file: <%s>' % fname)
            except:
                self.InteractiveTB()
                warn('Failure executing file: <%s>' % fname)

#************************* end of file <iplib.py> *****************************
