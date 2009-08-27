# -*- coding: utf-8 -*-
"""
Main IPython Component
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de>
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import __main__
import __builtin__
import StringIO
import bdb
import codeop
import exceptions
import glob
import keyword
import new
import os
import re
import shutil
import string
import sys
import tempfile

from IPython.core import ultratb
from IPython.core import debugger, oinspect
from IPython.core import shadowns
from IPython.core import history as ipcorehist
from IPython.core import prefilter
from IPython.core.autocall import IPyAutocall
from IPython.core.builtin_trap import BuiltinTrap
from IPython.core.fakemodule import FakeModule, init_fakemod_dict
from IPython.core.logger import Logger
from IPython.core.magic import Magic
from IPython.core.prompts import CachedOutput
from IPython.core.page import page
from IPython.core.component import Component
from IPython.core.oldusersetup import user_setup
from IPython.core.usage import interactive_usage, default_banner
from IPython.core.error import TryNext, UsageError

from IPython.extensions import pickleshare
from IPython.external.Itpl import ItplNS
from IPython.lib.backgroundjobs import BackgroundJobManager
from IPython.utils.ipstruct import Struct
from IPython.utils import PyColorize
from IPython.utils.genutils import *
from IPython.utils.strdispatch import StrDispatch
from IPython.utils.platutils import toggle_set_term_title, set_term_title

from IPython.utils.traitlets import (
    Int, Float, Str, CBool, CaselessStrEnum, Enum, List, Unicode
)

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------


# store the builtin raw_input globally, and use this always, in case user code
# overwrites it (like wx.py.PyShell does)
raw_input_original = raw_input

# compiled regexps for autoindent management
dedent_re = re.compile(r'^\s+raise|^\s+return|^\s+pass')


#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------


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


class SpaceInInput(exceptions.Exception): pass

class Bunch: pass

class InputList(list):
    """Class to store user input.

    It's basically a list, but slices return a string instead of a list, thus
    allowing things like (assuming 'In' is an instance):

    exec In[4:7]

    or

    exec In[5:9] + In[14] + In[21:25]"""

    def __getslice__(self,i,j):
        return ''.join(list.__getslice__(self,i,j))


class SyntaxTB(ultratb.ListTB):
    """Extension which holds some state: the last exception value"""

    def __init__(self,color_scheme = 'NoColor'):
        ultratb.ListTB.__init__(self,color_scheme)
        self.last_syntax_error = None

    def __call__(self, etype, value, elist):
        self.last_syntax_error = value
        ultratb.ListTB.__call__(self,etype,value,elist)

    def clear_err_state(self):
        """Return the current error state and clear it"""
        e = self.last_syntax_error
        self.last_syntax_error = None
        return e


def get_default_editor():
    try:
        ed = os.environ['EDITOR']
    except KeyError:
        if os.name == 'posix':
            ed = 'vi'  # the only one guaranteed to be there!
        else:
            ed = 'notepad' # same in Windows!
    return ed


class SeparateStr(Str):
    """A Str subclass to validate separate_in, separate_out, etc.

    This is a Str based traitlet that converts '0'->'' and '\\n'->'\n'.
    """

    def validate(self, obj, value):
        if value == '0': value = ''
        value = value.replace('\\n','\n')
        return super(SeparateStr, self).validate(obj, value)


#-----------------------------------------------------------------------------
# Main IPython class
#-----------------------------------------------------------------------------


class InteractiveShell(Component, Magic):
    """An enhanced, interactive shell for Python."""

    autocall = Enum((0,1,2), config_key='AUTOCALL')
    autoedit_syntax = CBool(False, config_key='AUTOEDIT_SYNTAX')
    autoindent = CBool(True, config_key='AUTOINDENT')
    automagic = CBool(True, config_key='AUTOMAGIC')
    display_banner = CBool(True, config_key='DISPLAY_BANNER')
    banner = Str('')
    banner1 = Str(default_banner, config_key='BANNER1')
    banner2 = Str('', config_key='BANNER2')
    c = Str('', config_key='C')
    cache_size = Int(1000, config_key='CACHE_SIZE')
    classic = CBool(False, config_key='CLASSIC')
    color_info = CBool(True, config_key='COLOR_INFO')
    colors = CaselessStrEnum(('NoColor','LightBG','Linux'), 
                             default_value='LightBG', config_key='COLORS')
    confirm_exit = CBool(True, config_key='CONFIRM_EXIT')
    debug = CBool(False, config_key='DEBUG')
    deep_reload = CBool(False, config_key='DEEP_RELOAD')
    embedded = CBool(False)
    embedded_active = CBool(False)
    editor = Str(get_default_editor(), config_key='EDITOR')
    filename = Str("<ipython console>")
    interactive = CBool(False, config_key='INTERACTIVE')
    ipythondir= Unicode('', config_key='IPYTHONDIR') # Set to os.getcwd() in __init__
    logstart = CBool(False, config_key='LOGSTART')
    logfile = Str('', config_key='LOGFILE')
    logplay = Str('', config_key='LOGPLAY')
    multi_line_specials = CBool(True, config_key='MULTI_LINE_SPECIALS')
    object_info_string_level = Enum((0,1,2), default_value=0,
                                    config_keys='OBJECT_INFO_STRING_LEVEL')
    pager = Str('less', config_key='PAGER')
    pdb = CBool(False, config_key='PDB')
    pprint = CBool(True, config_key='PPRINT')
    profile = Str('', config_key='PROFILE')
    prompt_in1 = Str('In [\\#]: ', config_key='PROMPT_IN1')
    prompt_in2 = Str('   .\\D.: ', config_key='PROMPT_IN2')
    prompt_out = Str('Out[\\#]: ', config_key='PROMPT_OUT1')
    prompts_pad_left = CBool(True, config_key='PROMPTS_PAD_LEFT')
    quiet = CBool(False, config_key='QUIET')

    readline_use = CBool(True, config_key='READLINE_USE')
    readline_merge_completions = CBool(True, 
                                       config_key='READLINE_MERGE_COMPLETIONS')
    readline_omit__names = Enum((0,1,2), default_value=0, 
                                config_key='READLINE_OMIT_NAMES')
    readline_remove_delims = Str('-/~', config_key='READLINE_REMOVE_DELIMS')
    readline_parse_and_bind = List([
            'tab: complete',
            '"\C-l": possible-completions',
            'set show-all-if-ambiguous on',
            '"\C-o": tab-insert',
            '"\M-i": "    "',
            '"\M-o": "\d\d\d\d"',
            '"\M-I": "\d\d\d\d"',
            '"\C-r": reverse-search-history',
            '"\C-s": forward-search-history',
            '"\C-p": history-search-backward',
            '"\C-n": history-search-forward',
            '"\e[A": history-search-backward',
            '"\e[B": history-search-forward',
            '"\C-k": kill-line',
            '"\C-u": unix-line-discard',
        ], allow_none=False, config_key='READLINE_PARSE_AND_BIND'
    )

    screen_length = Int(0, config_key='SCREEN_LENGTH')
    
    # Use custom TraitletTypes that convert '0'->'' and '\\n'->'\n'
    separate_in = SeparateStr('\n', config_key='SEPARATE_IN')
    separate_out = SeparateStr('', config_key='SEPARATE_OUT')
    separate_out2 = SeparateStr('', config_key='SEPARATE_OUT2')

    system_header = Str('IPython system call: ', config_key='SYSTEM_HEADER')
    system_verbose = CBool(False, config_key='SYSTEM_VERBOSE')
    term_title = CBool(False, config_key='TERM_TITLE')
    wildcards_case_sensitive = CBool(True, config_key='WILDCARDS_CASE_SENSITIVE')
    xmode = CaselessStrEnum(('Context','Plain', 'Verbose'), 
                            default_value='Context', config_key='XMODE')

    alias = List(allow_none=False, config_key='ALIAS')
    autoexec = List(allow_none=False)

    # class attribute to indicate whether the class supports threads or not.
    # Subclasses with thread support should override this as needed.
    isthreaded = False

    def __init__(self, parent=None, config=None, ipythondir=None, usage=None,
                 user_ns=None, user_global_ns=None,
                 banner1=None, banner2=None,
                 custom_exceptions=((),None)):

        # This is where traitlets with a config_key argument are updated
        # from the values on config.
        super(InteractiveShell, self).__init__(parent, config=config, name='__IP')

        # These are relatively independent and stateless
        self.init_ipythondir(ipythondir)
        self.init_instance_attrs()
        self.init_term_title()
        self.init_usage(usage)
        self.init_banner(banner1, banner2)

        # Create namespaces (user_ns, user_global_ns, alias_table, etc.)
        self.init_create_namespaces(user_ns, user_global_ns)
        # This has to be done after init_create_namespaces because it uses
        # something in self.user_ns, but before init_sys_modules, which
        # is the first thing to modify sys.
        self.save_sys_module_state()
        self.init_sys_modules()

        self.init_history()
        self.init_encoding()
        self.init_handlers()

        Magic.__init__(self, self)

        self.init_syntax_highlighting()
        self.init_hooks()
        self.init_pushd_popd_magic()
        self.init_traceback_handlers(custom_exceptions)
        self.init_user_ns()
        self.init_logger()
        self.init_aliases()
        self.init_builtins()
        
        # pre_config_initialization
        self.init_shadow_hist()

        # The next section should contain averything that was in ipmaker.
        self.init_logstart()

        # The following was in post_config_initialization
        self.init_inspector()
        self.init_readline()
        self.init_prompts()
        self.init_displayhook()
        self.init_reload_doctest()
        self.init_magics()
        self.init_pdb()
        self.hooks.late_startup_hook()

    def cleanup(self):
        self.restore_sys_module_state()

    #-------------------------------------------------------------------------
    # Traitlet changed handlers
    #-------------------------------------------------------------------------

    def _banner1_changed(self):
        self.compute_banner()

    def _banner2_changed(self):
        self.compute_banner()

    @property
    def usable_screen_length(self):
        if self.screen_length == 0:
            return 0
        else:
            num_lines_bot = self.separate_in.count('\n')+1
            return self.screen_length - num_lines_bot

    def _term_title_changed(self, name, new_value):
        self.init_term_title()

    #-------------------------------------------------------------------------
    # init_* methods called by __init__
    #-------------------------------------------------------------------------

    def init_ipythondir(self, ipythondir):
        if ipythondir is not None:
            self.ipythondir = ipythondir
            self.config.IPYTHONDIR = self.ipythondir
            return

        if hasattr(self.config, 'IPYTHONDIR'):
            self.ipythondir = self.config.IPYTHONDIR
        if not hasattr(self.config, 'IPYTHONDIR'):
            # cdw is always defined
            self.ipythondir = os.getcwd()

        # The caller must make sure that ipythondir exists.  We should
        # probably handle this using a Dir traitlet.
        if not os.path.isdir(self.ipythondir):
            raise IOError('IPython dir does not exist: %s' % self.ipythondir)

        # All children can just read this
        self.config.IPYTHONDIR = self.ipythondir

    def init_instance_attrs(self):
        self.jobs = BackgroundJobManager()
        self.more = False

        # command compiler
        self.compile = codeop.CommandCompiler()

        # User input buffer
        self.buffer = []

        # Make an empty namespace, which extension writers can rely on both
        # existing and NEVER being used by ipython itself.  This gives them a
        # convenient location for storing additional information and state
        # their extensions may require, without fear of collisions with other
        # ipython names that may develop later.
        self.meta = Struct()

        # Object variable to store code object waiting execution.  This is
        # used mainly by the multithreaded shells, but it can come in handy in
        # other situations.  No need to use a Queue here, since it's a single
        # item which gets cleared once run.
        self.code_to_run = None

        # Flag to mark unconditional exit
        self.exit_now = False

        # Temporary files used for various purposes.  Deleted at exit.
        self.tempfiles = []

        # Keep track of readline usage (later set by init_readline)
        self.has_readline = False

        # keep track of where we started running (mainly for crash post-mortem)
        # This is not being used anywhere currently.
        self.starting_dir = os.getcwd()

        # Indentation management
        self.indent_current_nsp = 0

    def init_term_title(self):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title('IPython: ' + abbrev_cwd())
        else:
            toggle_set_term_title(False)

    def init_usage(self, usage=None):
        if usage is None:
            self.usage = interactive_usage
        else:
            self.usage = usage

    def init_banner(self, banner1, banner2):
        if self.c:  # regular python doesn't print the banner with -c
            self.display_banner = False
        if banner1 is not None:
            self.banner1 = banner1
        if banner2 is not None:
            self.banner2 = banner2
        self.compute_banner()

    def compute_banner(self):
        self.banner = self.banner1 + '\n'
        if self.profile:
            self.banner += '\nIPython profile: %s\n' % self.profile
        if self.banner2:
            self.banner += '\n' + self.banner2 + '\n'        

    def init_create_namespaces(self, user_ns=None, user_global_ns=None):
        # Create the namespace where the user will operate.  user_ns is
        # normally the only one used, and it is passed to the exec calls as
        # the locals argument.  But we do carry a user_global_ns namespace
        # given as the exec 'globals' argument,  This is useful in embedding
        # situations where the ipython shell opens in a context where the
        # distinction between locals and globals is meaningful.  For
        # non-embedded contexts, it is just the same object as the user_ns dict.

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

        # These routines return properly built dicts as needed by the rest of
        # the code, and can also be used by extension writers to generate
        # properly initialized namespaces.
        user_ns, user_global_ns = self.make_user_namespaces(user_ns,
            user_global_ns)

        # Assign namespaces
        # This is the namespace where all normal user variables live
        self.user_ns = user_ns
        self.user_global_ns = user_global_ns

        # An auxiliary namespace that checks what parts of the user_ns were
        # loaded at startup, so we can list later only variables defined in
        # actual interactive use.  Since it is always a subset of user_ns, it
        # doesn't need to be seaparately tracked in the ns_table
        self.user_config_ns = {}

        # A namespace to keep track of internal data structures to prevent
        # them from cluttering user-visible stuff.  Will be updated later
        self.internal_ns = {}

        # Namespace of system aliases.  Each entry in the alias
        # table must be a 2-tuple of the form (N,name), where N is the number
        # of positional arguments of the alias.
        self.alias_table = {}

        # Now that FakeModule produces a real module, we've run into a nasty
        # problem: after script execution (via %run), the module where the user
        # code ran is deleted.  Now that this object is a true module (needed
        # so docetst and other tools work correctly), the Python module
        # teardown mechanism runs over it, and sets to None every variable
        # present in that module.  Top-level references to objects from the
        # script survive, because the user_ns is updated with them.  However,
        # calling functions defined in the script that use other things from
        # the script will fail, because the function's closure had references
        # to the original objects, which are now all None.  So we must protect
        # these modules from deletion by keeping a cache.
        # 
        # To avoid keeping stale modules around (we only need the one from the
        # last run), we use a dict keyed with the full path to the script, so
        # only the last version of the module is held in the cache.  Note,
        # however, that we must cache the module *namespace contents* (their
        # __dict__).  Because if we try to cache the actual modules, old ones
        # (uncached) could be destroyed while still holding references (such as
        # those held by GUI objects that tend to be long-lived)>
        # 
        # The %reset command will flush this cache.  See the cache_main_mod()
        # and clear_main_mod_cache() methods for details on use.

        # This is the cache used for 'main' namespaces
        self._main_ns_cache = {}
        # And this is the single instance of FakeModule whose __dict__ we keep
        # copying and clearing for reuse on each %run
        self._user_main_module = FakeModule()

        # A table holding all the namespaces IPython deals with, so that
        # introspection facilities can search easily.
        self.ns_table = {'user':user_ns,
                         'user_global':user_global_ns,
                         'alias':self.alias_table,
                         'internal':self.internal_ns,
                         'builtin':__builtin__.__dict__
                         }

        # Similarly, track all namespaces where references can be held and that
        # we can safely clear (so it can NOT include builtin).  This one can be
        # a simple list.
        self.ns_refs_table = [ user_ns, user_global_ns, self.user_config_ns,
                               self.alias_table, self.internal_ns,
                               self._main_ns_cache ]
        
    def init_sys_modules(self):
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

        # This is overridden in the InteractiveShellEmbed subclass to a no-op.

        try:
            main_name = self.user_ns['__name__']
        except KeyError:
            raise KeyError('user_ns dictionary MUST have a "__name__" key')
        else:
            sys.modules[main_name] = FakeModule(self.user_ns)

    def make_user_namespaces(self, user_ns=None, user_global_ns=None):
        """Return a valid local and global user interactive namespaces.

        This builds a dict with the minimal information needed to operate as a
        valid IPython user namespace, which you can pass to the various
        embedding classes in ipython. The default implementation returns the
        same dict for both the locals and the globals to allow functions to
        refer to variables in the namespace. Customized implementations can
        return different dicts. The locals dictionary can actually be anything
        following the basic mapping protocol of a dict, but the globals dict
        must be a true dict, not even a subclass. It is recommended that any
        custom object for the locals namespace synchronize with the globals
        dict somehow.

        Raises TypeError if the provided globals namespace is not a true dict.

        :Parameters:
            user_ns : dict-like, optional
                The current user namespace. The items in this namespace should
                be included in the output. If None, an appropriate blank
                namespace should be created.
            user_global_ns : dict, optional
                The current user global namespace. The items in this namespace
                should be included in the output. If None, an appropriate
                blank namespace should be created.

        :Returns:
            A tuple pair of dictionary-like object to be used as the local namespace
            of the interpreter and a dict to be used as the global namespace.
        """

        if user_ns is None:
            # Set __name__ to __main__ to better match the behavior of the
            # normal interpreter.
            user_ns = {'__name__'     :'__main__',
                       '__builtins__' : __builtin__,
                      }
        else:
            user_ns.setdefault('__name__','__main__')
            user_ns.setdefault('__builtins__',__builtin__)

        if user_global_ns is None:
            user_global_ns = user_ns
        if type(user_global_ns) is not dict:
            raise TypeError("user_global_ns must be a true dict; got %r"
                % type(user_global_ns))

        return user_ns, user_global_ns

    def init_history(self):
        # List of input with multi-line handling.
        self.input_hist = InputList()
        # This one will hold the 'raw' input history, without any
        # pre-processing.  This will allow users to retrieve the input just as
        # it was exactly typed in by the user, with %hist -r.
        self.input_hist_raw = InputList()

        # list of visited directories
        try:
            self.dir_hist = [os.getcwd()]
        except OSError:
            self.dir_hist = []

        # dict of output history
        self.output_hist = {}

        # Now the history file
        try:
            histfname = 'history-%s' % self.profile
        except AttributeError:
            histfname = 'history'
        self.histfile = os.path.join(self.config.IPYTHONDIR, histfname)

        # Fill the history zero entry, user counter starts at 1
        self.input_hist.append('\n')
        self.input_hist_raw.append('\n')

    def init_encoding(self):
        # Get system encoding at startup time.  Certain terminals (like Emacs
        # under Win32 have it set to None, and we need to have a known valid
        # encoding to use in the raw_input() method
        try:
            self.stdin_encoding = sys.stdin.encoding or 'ascii'
        except AttributeError:
            self.stdin_encoding = 'ascii'

    def init_handlers(self):
        # escapes for automatic behavior on the command line
        self.ESC_SHELL  = '!'
        self.ESC_SH_CAP = '!!'
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
                             self.ESC_SH_CAP : self.handle_shell_escape,
                             }

    def init_syntax_highlighting(self):
        # Python source parser/formatter for syntax highlighting
        pyformat = PyColorize.Parser().format
        self.pycolorize = lambda src: pyformat(src,'str',self.colors)

    def init_hooks(self):
        # hooks holds pointers used for user-side customizations
        self.hooks = Struct()
        
        self.strdispatchers = {}
        
        # Set all default hooks, defined in the IPython.hooks module.
        import IPython.core.hooks
        hooks = IPython.core.hooks
        for hook_name in hooks.__all__:
            # default hooks have priority 100, i.e. low; user hooks should have
            # 0-100 priority
            self.set_hook(hook_name,getattr(hooks,hook_name), 100)

    def init_pushd_popd_magic(self):
        # for pushd/popd management
        try:
            self.home_dir = get_home_dir()
        except HomeDirError, msg:
            fatal(msg)

        self.dir_stack = []

    def init_traceback_handlers(self, custom_exceptions):
        # Syntax error handler.
        self.SyntaxTB = SyntaxTB(color_scheme='NoColor')
        
        # The interactive one is initialized with an offset, meaning we always
        # want to remove the topmost item in the traceback, which is our own
        # internal code. Valid modes: ['Plain','Context','Verbose']
        self.InteractiveTB = ultratb.AutoFormattedTB(mode = 'Plain',
                                                     color_scheme='NoColor',
                                                     tb_offset = 1)

        # IPython itself shouldn't crash. This will produce a detailed
        # post-mortem if it does.  But we only install the crash handler for
        # non-threaded shells, the threaded ones use a normal verbose reporter
        # and lose the crash handler.  This is because exceptions in the main
        # thread (such as in GUI code) propagate directly to sys.excepthook,
        # and there's no point in printing crash dumps for every user exception.
        if self.isthreaded:
            ipCrashHandler = ultratb.FormattedTB()
        else:
            from IPython.core import crashhandler
            ipCrashHandler = crashhandler.IPythonCrashHandler(self)
        self.set_crash_handler(ipCrashHandler)

        # and add any custom exception handlers the user may have specified
        self.set_custom_exc(*custom_exceptions)

    def init_logger(self):
        self.logger = Logger(self, logfname='ipython_log.py', logmode='rotate')
        # local shortcut, this is used a LOT
        self.log = self.logger.log
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

    def init_logstart(self):
        if self.logplay:
            self.magic_logstart(self.logplay + ' append')
        elif  self.logfile:
            self.magic_logstart(self.logfile)
        elif self.logstart:
            self.magic_logstart()

    def init_aliases(self):
        # dict of things NOT to alias (keywords, builtins and some magics)
        no_alias = {}
        no_alias_magics = ['cd','popd','pushd','dhist','alias','unalias']
        for key in keyword.kwlist + no_alias_magics:
            no_alias[key] = 1
        no_alias.update(__builtin__.__dict__)
        self.no_alias = no_alias

        # Make some aliases automatically
        # Prepare list of shell aliases to auto-define
        if os.name == 'posix':
            auto_alias = ('mkdir mkdir', 'rmdir rmdir',
                          'mv mv -i','rm rm -i','cp cp -i',
                          'cat cat','less less','clear clear',
                          # a better ls
                          'ls ls -F',
                          # long ls
                          'll ls -lF')
            # Extra ls aliases with color, which need special treatment on BSD
            # variants
            ls_extra = ( # color ls
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
            # The BSDs don't ship GNU ls, so they don't understand the
            # --color switch out of the box
            if 'bsd' in sys.platform:
                ls_extra = ( # ls normal files only
                             'lf ls -lF | grep ^-',
                             # ls symbolic links
                             'lk ls -lF | grep ^l',
                             # directories or links to directories,
                             'ldir ls -lF | grep /$',
                             # things which are executable
                             'lx ls -lF | grep ^-..x',
                             )
            auto_alias = auto_alias + ls_extra
        elif os.name in ['nt','dos']:
            auto_alias = ('ls dir /on',
                          'ddir dir /ad /on', 'ldir dir /ad /on',
                          'mkdir mkdir','rmdir rmdir','echo echo',
                          'ren ren','cls cls','copy copy')
        else:
            auto_alias = ()
        self.auto_alias = [s.split(None,1) for s in auto_alias]
        
        # Load default aliases
        for alias, cmd in self.auto_alias:
            self.define_alias(alias,cmd)

        # Load user aliases
        for alias in self.alias:
            self.magic_alias(alias)

    def init_builtins(self):
        self.builtin_trap = BuiltinTrap(self)

    def init_shadow_hist(self):
        try:
            self.db = pickleshare.PickleShareDB(self.config.IPYTHONDIR + "/db")
        except exceptions.UnicodeDecodeError:
            print "Your ipythondir can't be decoded to unicode!"
            print "Please set HOME environment variable to something that"
            print r"only has ASCII characters, e.g. c:\home"
            print "Now it is", self.config.IPYTHONDIR
            sys.exit()
        self.shadowhist = ipcorehist.ShadowHist(self.db)

    def init_inspector(self):
        # Object inspector
        self.inspector = oinspect.Inspector(oinspect.InspectColors,
                                            PyColorize.ANSICodeColors,
                                            'NoColor',
                                            self.object_info_string_level)

    def init_readline(self):
        """Command history completion/saving/reloading."""

        self.rl_next_input = None
        self.rl_do_indent = False

        if not self.readline_use:
            return

        import IPython.utils.rlineimpl as readline
                  
        if not readline.have_readline:
            self.has_readline = 0
            self.readline = None
            # no point in bugging windows users with this every time:
            warn('Readline services not available on this platform.')
        else:
            sys.modules['readline'] = readline
            import atexit
            from IPython.core.completer import IPCompleter
            self.Completer = IPCompleter(self,
                                            self.user_ns,
                                            self.user_global_ns,
                                            self.readline_omit__names,
                                            self.alias_table)
            sdisp = self.strdispatchers.get('complete_command', StrDispatch())
            self.strdispatchers['complete_command'] = sdisp
            self.Completer.custom_completers = sdisp
            # Platform-specific configuration
            if os.name == 'nt':
                self.readline_startup_hook = readline.set_pre_input_hook
            else:
                self.readline_startup_hook = readline.set_startup_hook

            # Load user's initrc file (readline config)
            # Or if libedit is used, load editrc.
            inputrc_name = os.environ.get('INPUTRC')
            if inputrc_name is None:
                home_dir = get_home_dir()
                if home_dir is not None:
                    inputrc_name = '.inputrc'
                    if readline.uses_libedit:
                        inputrc_name = '.editrc'
                    inputrc_name = os.path.join(home_dir, inputrc_name)
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
            self.set_completer()

            # Configure readline according to user's prefs
            # This is only done if GNU readline is being used.  If libedit
            # is being used (as on Leopard) the readline config is
            # not run as the syntax for libedit is different.
            if not readline.uses_libedit:
                for rlcommand in self.readline_parse_and_bind:
                    #print "loading rl:",rlcommand  # dbg
                    readline.parse_and_bind(rlcommand)

            # Remove some chars from the delimiters list.  If we encounter
            # unicode chars, discard them.
            delims = readline.get_completer_delims().encode("ascii", "ignore")
            delims = delims.translate(string._idmap,
                                      self.readline_remove_delims)
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
        self.set_autoindent(self.autoindent)

    def init_prompts(self):
        # Initialize cache, set in/out prompts and printing system
        self.outputcache = CachedOutput(self,
                                        self.cache_size,
                                        self.pprint,
                                        input_sep = self.separate_in,
                                        output_sep = self.separate_out,
                                        output_sep2 = self.separate_out2,
                                        ps1 = self.prompt_in1,
                                        ps2 = self.prompt_in2,
                                        ps_out = self.prompt_out,
                                        pad_left = self.prompts_pad_left)

        # user may have over-ridden the default print hook:
        try:
            self.outputcache.__class__.display = self.hooks.display
        except AttributeError:
            pass

    def init_displayhook(self):
        # I don't like assigning globally to sys, because it means when
        # embedding instances, each embedded instance overrides the previous
        # choice. But sys.displayhook seems to be called internally by exec,
        # so I don't see a way around it.  We first save the original and then
        # overwrite it.
        self.sys_displayhook = sys.displayhook
        sys.displayhook = self.outputcache

    def init_reload_doctest(self):
        # Do a proper resetting of doctest, including the necessary displayhook
        # monkeypatching
        try:
            doctest_reload()
        except ImportError:
            warn("doctest module does not exist.")

    def init_magics(self):
        # Set user colors (don't do it in the constructor above so that it
        # doesn't crash if colors option is invalid)
        self.magic_colors(self.colors)

    def init_pdb(self):
        # Set calling of pdb on exceptions
        # self.call_pdb is a property
        self.call_pdb = self.pdb

    # def init_exec_commands(self):
    #     for cmd in self.config.EXECUTE:
    #         print "execute:", cmd
    #         self.api.runlines(cmd)
    #         
    #     batchrun = False
    #     if self.config.has_key('EXECFILE'):
    #         for batchfile in [path(arg) for arg in self.config.EXECFILE
    #             if arg.lower().endswith('.ipy')]:
    #             if not batchfile.isfile():
    #                 print "No such batch file:", batchfile
    #                 continue
    #             self.api.runlines(batchfile.text())
    #             batchrun = True
    #     # without -i option, exit after running the batch file
    #     if batchrun and not self.interactive:
    #         self.ask_exit()            

    # def load(self, mod):
    #     """ Load an extension.
    #     
    #     Some modules should (or must) be 'load()':ed, rather than just imported.
    #     
    #     Loading will do:
    #     
    #     - run init_ipython(ip)
    #     - run ipython_firstrun(ip)
    #     """
    # 
    #     if mod in self.extensions:
    #         # just to make sure we don't init it twice
    #         # note that if you 'load' a module that has already been
    #         # imported, init_ipython gets run anyway
    #         
    #         return self.extensions[mod]
    #     __import__(mod)
    #     m = sys.modules[mod]
    #     if hasattr(m,'init_ipython'):
    #         m.init_ipython(self)
    #         
    #     if hasattr(m,'ipython_firstrun'):
    #         already_loaded = self.db.get('firstrun_done', set())
    #         if mod not in already_loaded:
    #             m.ipython_firstrun(self)
    #             already_loaded.add(mod)
    #             self.db['firstrun_done'] = already_loaded
    #         
    #     self.extensions[mod] = m
    #     return m

    def init_user_ns(self):
        """Initialize all user-visible namespaces to their minimum defaults.

        Certain history lists are also initialized here, as they effectively
        act as user namespaces.

        Notes
        -----
        All data structures here are only filled in, they are NOT reset by this
        method.  If they were not empty before, data will simply be added to
        therm.
        """
        # The user namespace MUST have a pointer to the shell itself.
        self.user_ns[self.name] = self

        # Store myself as the public api!!!
        self.user_ns['_ip'] = self

        # make global variables for user access to the histories
        self.user_ns['_ih'] = self.input_hist
        self.user_ns['_oh'] = self.output_hist
        self.user_ns['_dh'] = self.dir_hist

        # user aliases to input and output histories
        self.user_ns['In']  = self.input_hist
        self.user_ns['Out'] = self.output_hist

        self.user_ns['_sh'] = shadowns

        # Put 'help' in the user namespace
        try:
            from site import _Helper
            self.user_ns['help'] = _Helper()
        except ImportError:
            warn('help() not available - check site.py')

    def save_sys_module_state(self):
        """Save the state of hooks in the sys module.

        This has to be called after self.user_ns is created.
        """
        self._orig_sys_module_state = {}
        self._orig_sys_module_state['stdin'] = sys.stdin
        self._orig_sys_module_state['stdout'] = sys.stdout
        self._orig_sys_module_state['stderr'] = sys.stderr
        self._orig_sys_module_state['displayhook'] = sys.displayhook
        self._orig_sys_module_state['excepthook'] = sys.excepthook
        try:
            self._orig_sys_modules_main_name = self.user_ns['__name__']
        except KeyError:
            pass

    def restore_sys_module_state(self):
        """Restore the state of the sys module."""
        try:
            for k, v in self._orig_sys_module_state.items():
                setattr(sys, k, v)
        except AttributeError:
            pass
        try:
            delattr(sys, 'ipcompleter')
        except AttributeError:
            pass
        # Reset what what done in self.init_sys_modules
        try:
            sys.modules[self.user_ns['__name__']] = self._orig_sys_modules_main_name
        except (AttributeError, KeyError):
            pass

    def set_hook(self,name,hook, priority = 50, str_key = None, re_key = None):
        """set_hook(name,hook) -> sets an internal IPython hook.

        IPython exposes some of its internal API as user-modifiable hooks.  By
        adding your function to one of these hooks, you can modify IPython's 
        behavior to call at runtime your own routines."""

        # At some point in the future, this should validate the hook before it
        # accepts it.  Probably at least check that the hook takes the number
        # of args it's supposed to.
        
        f = new.instancemethod(hook,self,self.__class__)

        # check if the hook is for strdispatcher first
        if str_key is not None:
            sdp = self.strdispatchers.get(name, StrDispatch())
            sdp.add_s(str_key, f, priority )
            self.strdispatchers[name] = sdp
            return
        if re_key is not None:
            sdp = self.strdispatchers.get(name, StrDispatch())
            sdp.add_re(re.compile(re_key), f, priority )
            self.strdispatchers[name] = sdp
            return
            
        dp = getattr(self.hooks, name, None)
        if name not in IPython.core.hooks.__all__:
            print "Warning! Hook '%s' is not one of %s" % (name, IPython.core.hooks.__all__ )
        if not dp:
            dp = IPython.core.hooks.CommandChainDispatcher()
        
        try:
            dp.add(f,priority)
        except AttributeError:
            # it was not commandchain, plain old func - replace
            dp = f

        setattr(self.hooks,name, dp)

    def set_crash_handler(self, crashHandler):
        """Set the IPython crash handler.

        This must be a callable with a signature suitable for use as
        sys.excepthook."""

        # Install the given crash handler as the Python exception hook
        sys.excepthook = crashHandler
        
        # The instance will store a pointer to this, so that runtime code
        # (such as magics) can access it.  This is because during the
        # read-eval loop, it gets temporarily overwritten (to deal with GUI
        # frameworks).
        self.sys_excepthook = sys.excepthook

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

    def set_completer(self):
        """reset readline's completer to be our own."""
        self.readline.set_completer(self.Completer.complete)
        
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

    def magic(self,arg_s):
        """Call a magic function by name.

        Input: a string containing the name of the magic function to call and any
        additional arguments to be passed to the magic.

        magic('name -opt foo bar') is equivalent to typing at the ipython
        prompt:

        In[1]: %name -opt foo bar

        To call a magic without arguments, simply use magic('name').

        This provides a proper Python function to call IPython's magics in any
        valid Python code you can type at the interpreter, including loops and
        compound statements.
        """

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
            magic_args = self.var_expand(magic_args,1)
            with self.builtin_trap:
                result = fn(magic_args)
            return result

    def define_magic(self, magicname, func):
        """Expose own function as magic function for ipython 
    
        def foo_impl(self,parameter_s=''):
            'My very own magic!. (Use docstrings, IPython reads them).'
            print 'Magic function. Passed parameter is between < >:'
            print '<%s>' % parameter_s
            print 'The self object is:',self
    
        self.define_magic('foo',foo_impl)
        """
        
        import new
        im = new.instancemethod(func,self, self.__class__)
        old = getattr(self, "magic_" + magicname, None)
        setattr(self, "magic_" + magicname, im)
        return old

    def define_macro(self, name, themacro):
        """Define a new macro

        Parameters
        ----------
        name : str
            The name of the macro.
        themacro : str or Macro
            The action to do upon invoking the macro.  If a string, a new 
            Macro object is created by passing the string to it.
        """
        
        from IPython.core import macro

        if isinstance(themacro, basestring):
            themacro = macro.Macro(themacro)
        if not isinstance(themacro, macro.Macro):
            raise ValueError('A macro must be a string or a Macro instance.')
        self.user_ns[name] = themacro

    def define_alias(self, name, cmd):
        """ Define a new alias."""

        if callable(cmd):
            self.alias_table[name] = cmd
            from IPython.core import shadowns
            setattr(shadowns, name, cmd)
            return

        if isinstance(cmd, basestring):
            nargs = cmd.count('%s')
            if nargs>0 and cmd.find('%l')>=0:
                raise Exception('The %s and %l specifiers are mutually '
                                'exclusive in alias definitions.')
                  
            self.alias_table[name] = (nargs,cmd)
            return
        
        self.alias_table[name] = cmd

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

    def system(self, cmd):
        """Make a system call, using IPython."""
        return self.hooks.shell_hook(self.var_expand(cmd, depth=2))

    def ex(self, cmd):
        """Execute a normal python statement in user namespace."""
        with self.builtin_trap:
            exec cmd in self.user_global_ns, self.user_ns

    def ev(self, expr):
        """Evaluate python expression expr in user namespace.

        Returns the result of evaluation
        """
        with self.builtin_trap:
            result = eval(expr, self.user_global_ns, self.user_ns)
        return result

    def getoutput(self, cmd):
        return getoutput(self.var_expand(cmd,depth=2),
                         header=self.system_header,
                         verbose=self.system_verbose)

    def getoutputerror(self, cmd):
        return getoutputerror(self.var_expand(cmd,depth=2),
                              header=self.system_header,
                              verbose=self.system_verbose)

    def complete(self, text):
        """Return a sorted list of all possible completions on text.

        Inputs:

          - text: a string of text to be completed on.

        This is a wrapper around the completion mechanism, similar to what
        readline does at the command line when the TAB key is hit.  By
        exposing it as a method, it can be used by other non-readline
        environments (such as GUIs) for text completion.

        Simple usage example:

        In [7]: x = 'hello'

        In [8]: x
        Out[8]: 'hello'

        In [9]: print x
        hello

        In [10]: _ip.complete('x.l')
        Out[10]: ['x.ljust', 'x.lower', 'x.lstrip']
        """

        # Inject names into __builtin__ so we can complete on the added names.
        with self.builtin_trap:
            complete = self.Completer.complete
            state = 0
            # use a dict so we get unique keys, since ipyhton's multiple
            # completers can return duplicates.  When we make 2.4 a requirement,
            # start using sets instead, which are faster.
            comps = {}
            while True:
                newcomp = complete(text,state,line_buffer=text)
                if newcomp is None:
                    break
                comps[newcomp] = 1
                state += 1
            outcomps = comps.keys()
            outcomps.sort()
            #print "T:",text,"OC:",outcomps  # dbg
            #print "vars:",self.user_ns.keys()
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
            self.define_alias(alias,cmd)

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

    def set_next_input(self, s):
        """ Sets the 'default' input string for the next command line.
        
        Requires readline.
        
        Example:
        
        [D:\ipython]|1> _ip.set_next_input("Hello Word")
        [D:\ipython]|2> Hello Word_  # cursor is here        
        """

        self.rl_next_input = s

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

        # Clear all user namespaces to release all references cleanly.
        self.reset()

        # Run user hooks
        self.hooks.shutdown_hook()

    def reset(self):
        """Clear all internal namespaces.

        Note that this is much more aggressive than %reset, since it clears
        fully all namespaces, as well as all input/output lists.
        """
        for ns in self.ns_refs_table:
            ns.clear()

        # Clear input and output histories
        self.input_hist[:] = []
        self.input_hist_raw[:] = []
        self.output_hist.clear()
        # Restore the user namespaces to minimal usability
        self.init_user_ns()
        
    def savehist(self):
        """Save input history to a file (via readline library)."""

        if not self.has_readline:
            return
        
        try:
            self.readline.write_history_file(self.histfile)
        except:
            print 'Unable to save IPython command history to file: ' + \
                  `self.histfile`

    def reloadhist(self):
        """Reload the input history from disk file."""

        if self.has_readline:
            try:
                self.readline.clear_history()
                self.readline.read_history_file(self.shell.histfile)
            except AttributeError:
                pass
            

    def history_saving_wrapper(self, func):
        """ Wrap func for readline history saving
        
        Convert func into callable that saves & restores
        history around the call """
        
        if not self.has_readline:
            return func
        
        def wrapper():
            self.savehist()
            try:
                func()
            finally:
                readline.read_history_file(self.histfile)
        return wrapper
            
    def pre_readline(self):
        """readline hook to be used at the start of each line.

        Currently it handles auto-indent only."""

        #debugx('self.indent_current_nsp','pre_readline:')

        if self.rl_do_indent:
            self.readline.insert_text(self.indent_current_str())
        if self.rl_next_input is not None:
            self.readline.insert_text(self.rl_next_input)
            self.rl_next_input = None

    def ask_yes_no(self,prompt,default=True):
        if self.quiet:
            return True
        return ask_yes_no(prompt,default)

    def new_main_mod(self,ns=None):
        """Return a new 'main' module object for user code execution.
        """
        main_mod = self._user_main_module
        init_fakemod_dict(main_mod,ns)
        return main_mod

    def cache_main_mod(self,ns,fname):
        """Cache a main module's namespace.

        When scripts are executed via %run, we must keep a reference to the
        namespace of their __main__ module (a FakeModule instance) around so
        that Python doesn't clear it, rendering objects defined therein
        useless.

        This method keeps said reference in a private dict, keyed by the
        absolute path of the module object (which corresponds to the script
        path).  This way, for multiple executions of the same script we only
        keep one copy of the namespace (the last one), thus preventing memory
        leaks from old references while allowing the objects from the last
        execution to be accessible.

        Note: we can not allow the actual FakeModule instances to be deleted,
        because of how Python tears down modules (it hard-sets all their
        references to None without regard for reference counts).  This method
        must therefore make a *copy* of the given namespace, to allow the
        original module's __dict__ to be cleared and reused.

        
        Parameters
        ----------
          ns : a namespace (a dict, typically)

          fname : str
            Filename associated with the namespace.

        Examples
        --------

        In [10]: import IPython

        In [11]: _ip.cache_main_mod(IPython.__dict__,IPython.__file__)

        In [12]: IPython.__file__ in _ip._main_ns_cache
        Out[12]: True
        """
        self._main_ns_cache[os.path.abspath(fname)] = ns.copy()

    def clear_main_mod_cache(self):
        """Clear the cache of main modules.

        Mainly for use by utilities like %reset.

        Examples
        --------

        In [15]: import IPython

        In [16]: _ip.cache_main_mod(IPython.__dict__,IPython.__file__)

        In [17]: len(_ip._main_ns_cache) > 0
        Out[17]: True

        In [18]: _ip.clear_main_mod_cache()

        In [19]: len(_ip._main_ns_cache) == 0
        Out[19]: True
        """
        self._main_ns_cache.clear()

    def _should_recompile(self,e):
        """Utility routine for edit_syntax_error"""

        if e.filename in ('<ipython console>','<input>','<string>',
                          '<console>','<BackgroundJob compilation>',
                          None):
                              
            return False
        try:
            if (self.autoedit_syntax and 
                not self.ask_yes_no('Return to editor to correct syntax error? '
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
        try:
            self.hooks.fix_error_editor(e.filename,
                int0(e.lineno),int0(e.offset),e.msg)
        except TryNext:
            warn('Could not open editor')
            return False
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
                self.safe_execfile(err.filename,self.user_ns)
            except:
                self.showtraceback()
            else:
                try:
                    f = file(err.filename)
                    try:
                        sys.displayhook(f.read())
                    finally:
                        f.close()
                except:
                    self.showtraceback()

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

    def debugger(self,force=False):
        """Call the pydb/pdb debugger.

        Keywords:

          - force(False): by default, this routine checks the instance call_pdb
          flag and does not actually invoke the debugger if the flag is false.
          The 'force' option forces the debugger to activate even if the flag
          is false.
        """

        if not (force or self.call_pdb):
            return

        if not hasattr(sys,'last_traceback'):
            error('No traceback has been produced, nothing to debug.')
            return

        # use pydb if available
        if debugger.has_pydb:
            from pydb import pm
        else:
            # fallback to our internal debugger
            pm = lambda : self.InteractiveTB.debugger(force=True)
        self.history_saving_wrapper(pm)()

    def showtraceback(self,exc_tuple = None,filename=None,tb_offset=None):
        """Display the exception that just occurred.

        If nothing is known about the exception, this is the method which
        should be used throughout the code for presenting user tracebacks,
        rather than directly invoking the InteractiveTB object.

        A specific showsyntaxerror() also exists, but this method can take
        care of calling it if needed, so unless you are explicitly catching a
        SyntaxError exception, don't try to analyze the stack manually and
        simply call this method."""

        
        # Though this won't be called by syntax errors in the input line,
        # there may be SyntaxError cases whith imported code.
        
        try:
            if exc_tuple is None:
                etype, value, tb = sys.exc_info()
            else:
                etype, value, tb = exc_tuple
    
            if etype is SyntaxError:
                self.showsyntaxerror(filename)
            elif etype is UsageError:
                print "UsageError:", value
            else:
                # WARNING: these variables are somewhat deprecated and not
                # necessarily safe to use in a threaded environment, but tools
                # like pdb depend on their existence, so let's set them.  If we
                # find problems in the field, we'll need to revisit their use.
                sys.last_type = etype
                sys.last_value = value
                sys.last_traceback = tb
    
                if etype in self.custom_exceptions:
                    self.CustomTB(etype,value,tb)
                else:
                    self.InteractiveTB(etype,value,tb,tb_offset=tb_offset)
                    if self.InteractiveTB.call_pdb and self.has_readline:
                        # pdb mucks up readline, fix it back
                        self.set_completer()
        except KeyboardInterrupt:
            self.write("\nKeyboardInterrupt\n")

    def mainloop(self, banner=None):
        """Start the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner.
        """
        
        with self.builtin_trap:
            if self.c:  # Emulate Python's -c option
                self.exec_init_cmd()

            if self.display_banner:
                if banner is None:
                    banner = self.banner

            # if you run stuff with -c <cmd>, raw hist is not updated
            # ensure that it's in sync
            if len(self.input_hist) != len (self.input_hist_raw):
                self.input_hist_raw = InputList(self.input_hist)

            while 1:
                try:
                    self.interact()
                    #self.interact_with_readline()                
                    # XXX for testing of a readline-decoupled repl loop, call
                    # interact_with_readline above
                    break
                except KeyboardInterrupt:
                    # this should not be necessary, but KeyboardInterrupt
                    # handling seems rather unpredictable...
                    self.write("\nKeyboardInterrupt in interact()\n")

    def exec_init_cmd(self):
        """Execute a command given at the command line.

        This emulates Python's -c option."""

        #sys.argv = ['-c']
        self.push_line(self.prefilter(self.c, False))
        if not self.interactive:
            self.ask_exit()

    def interact_prompt(self):
        """ Print the prompt (in read-eval-print loop) 

        Provided for those who want to implement their own read-eval-print loop (e.g. GUIs), not 
        used in standard IPython flow.
        """
        if self.more:
            try:
                prompt = self.hooks.generate_prompt(True)
            except:
                self.showtraceback()
            if self.autoindent:
                self.rl_do_indent = True

        else:
            try:
                prompt = self.hooks.generate_prompt(False)
            except:
                self.showtraceback()
        self.write(prompt)

    def interact_handle_input(self,line):
        """ Handle the input line (in read-eval-print loop)
        
        Provided for those who want to implement their own read-eval-print loop (e.g. GUIs), not 
        used in standard IPython flow.        
        """
        if line.lstrip() == line:
            self.shadowhist.add(line.strip())
        lineout = self.prefilter(line,self.more)

        if line.strip():
            if self.more:
                self.input_hist_raw[-1] += '%s\n' % line
            else:
                self.input_hist_raw.append('%s\n' % line)                

        
        self.more = self.push_line(lineout)
        if (self.SyntaxTB.last_syntax_error and
            self.autoedit_syntax):
            self.edit_syntax_error()

    def interact_with_readline(self):
        """ Demo of using interact_handle_input, interact_prompt
        
        This is the main read-eval-print loop. If you need to implement your own (e.g. for GUI),
        it should work like this.
        """ 
        self.readline_startup_hook(self.pre_readline)
        while not self.exit_now:
            self.interact_prompt()
            if self.more:
                self.rl_do_indent = True
            else:
                self.rl_do_indent = False
            line = raw_input_original().decode(self.stdin_encoding)
            self.interact_handle_input(line)

    def interact(self, banner=None):
        """Closely emulate the interactive Python console."""

        # batch run -> do not interact        
        if self.exit_now:
            return

        if self.display_banner:
            if banner is None:
                banner = self.banner
            self.write(banner)

        more = 0
        
        # Mark activity in the builtins
        __builtin__.__dict__['__IPYTHON__active'] += 1
        
        if self.has_readline:
            self.readline_startup_hook(self.pre_readline)
        # exit_now is set by a call to %Exit or %Quit, through the
        # ask_exit callback.
        
        while not self.exit_now:
            self.hooks.pre_prompt_hook()
            if more:
                try:
                    prompt = self.hooks.generate_prompt(True)
                except:
                    self.showtraceback()
                if self.autoindent:
                    self.rl_do_indent = True
                    
            else:
                try:
                    prompt = self.hooks.generate_prompt(False)
                except:
                    self.showtraceback()
            try:
                line = self.raw_input(prompt, more)
                if self.exit_now:
                    # quick exit on sys.std[in|out] close
                    break
                if self.autoindent:
                    self.rl_do_indent = False
                    
            except KeyboardInterrupt:
                #double-guard against keyboardinterrupts during kbdint handling
                try:
                    self.write('\nKeyboardInterrupt\n')
                    self.resetbuffer()
                    # keep cache in sync with the prompt counter:
                    self.outputcache.prompt_count -= 1
    
                    if self.autoindent:
                        self.indent_current_nsp = 0
                    more = 0
                except KeyboardInterrupt:
                    pass
            except EOFError:
                if self.autoindent:
                    self.rl_do_indent = False
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
                more = self.push_line(line)
                if (self.SyntaxTB.last_syntax_error and
                    self.autoedit_syntax):
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

    def expand_alias(self, line):
        """ Expand an alias in the command line 
        
        Returns the provided command line, possibly with the first word 
        (command) translated according to alias expansion rules.
        
        [ipython]|16> _ip.expand_aliases("np myfile.txt")
                 <16> 'q:/opt/np/notepad++.exe myfile.txt'
        """
        
        pre,fn,rest = self.split_user_input(line)
        res = pre + self.expand_aliases(fn, rest)
        return res

    def expand_aliases(self, fn, rest):
        """Expand multiple levels of aliases:
        
        if:
        
        alias foo bar /tmp
        alias baz foo
        
        then:
        
        baz huhhahhei -> bar /tmp huhhahhei
        
        """
        line = fn + " " + rest
        
        done = set()
        while 1:
            pre,fn,rest = prefilter.splitUserInput(line,
                                                   prefilter.shell_line_split)
            if fn in self.alias_table:
                if fn in done:
                    warn("Cyclic alias definition, repeated '%s'" % fn)
                    return ""
                done.add(fn)

                l2 = self.transform_alias(fn,rest)
                # dir -> dir 
                # print "alias",line, "->",l2  #dbg
                if l2 == line:
                    break
                # ls -> ls -F should not recurse forever
                if l2.split(None,1)[0] == line.split(None,1)[0]:
                    line = l2
                    break
                
                line=l2
                
                
                # print "al expand to",line #dbg
            else:
                break
                
        return line

    def transform_alias(self, alias,rest=''):
        """ Transform alias to system command string.
        """
        trg = self.alias_table[alias]

        nargs,cmd = trg
        # print trg #dbg
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
        #print 'new command: <%r>' % cmd  # dbg
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

    def push(self, variables, interactive=True):
        """Inject a group of variables into the IPython user namespace.

        Parameters
        ----------
        variables : dict, str or list/tuple of str
            The variables to inject into the user's namespace.  If a dict,
            a simple update is done.  If a str, the string is assumed to 
            have variable names separated by spaces.  A list/tuple of str
            can also be used to give the variable names.  If just the variable
            names are give (list/tuple/str) then the variable values looked
            up in the callers frame.
        interactive : bool
            If True (default), the variables will be listed with the ``who``
            magic.
        """
        vdict = None

        # We need a dict of name/value pairs to do namespace updates.
        if isinstance(variables, dict):
            vdict = variables
        elif isinstance(variables, (basestring, list, tuple)):
            if isinstance(variables, basestring):
                vlist = variables.split()
            else:
                vlist = variables
            vdict = {}
            cf = sys._getframe(1)
            for name in vlist:
                try:
                    vdict[name] = eval(name, cf.f_globals, cf.f_locals)
                except:
                    print ('Could not get variable %s from %s' %
                           (name,cf.f_code.co_name))
        else:
            raise ValueError('variables must be a dict/str/list/tuple')
            
        # Propagate variables to user namespace
        self.user_ns.update(vdict)

        # And configure interactive visibility
        config_ns = self.user_config_ns
        if interactive:
            for name, val in vdict.iteritems():
                config_ns.pop(name, None)
        else:
            for name,val in vdict.iteritems():
                config_ns[name] = val

    def cleanup_ipy_script(self, script):
        """Make a script safe for self.runlines()

        Notes
        -----
        This was copied over from the old ipapi and probably can be done
        away with once we move to block based interpreter.
        
        - Removes empty lines Suffixes all indented blocks that end with
        - unindented lines with empty lines
        """
        
        res = []
        lines = script.splitlines()

        level = 0
        for l in lines:
            lstripped = l.lstrip()
            stripped = l.strip()                
            if not stripped:
                continue
            newlevel = len(l) - len(lstripped)
            def is_secondary_block_start(s):
                if not s.endswith(':'):
                    return False
                if (s.startswith('elif') or 
                    s.startswith('else') or 
                    s.startswith('except') or
                    s.startswith('finally')):
                    return True
                    
            if level > 0 and newlevel == 0 and \
                   not is_secondary_block_start(stripped): 
                # add empty line
                res.append('')
                
            res.append(l)
            level = newlevel
        return '\n'.join(res) + '\n'

    def runlines(self, lines, clean=False):
        """Run a string of one or more lines of source.

        This method is capable of running a string containing multiple source
        lines, as if they had been entered at the IPython prompt.  Since it
        exposes IPython's processing machinery, the given strings can contain
        magic calls (%magic), special shell access (!cmd), etc.
        """

        if isinstance(lines, (list, tuple)):
            lines = '\n'.join(lines)

        if clean:
            lines = self.cleanup_ipy_script(lines)

        # We must start with a clean buffer, in case this is run from an
        # interactive IPython session (via a magic, for example).
        self.resetbuffer()
        lines = lines.splitlines()
        more = 0

        with self.builtin_trap:
            for line in lines:
                # skip blank lines so we don't mess up the prompt counter, but do
                # NOT skip even a blank line if we are in a code block (more is
                # true)
            
                if line or more:
                    # push to raw history, so hist line numbers stay in sync
                    self.input_hist_raw.append("# " + line + "\n")
                    more = self.push_line(self.prefilter(line,more))
                    # IPython's runsource returns None if there was an error
                    # compiling the code.  This allows us to stop processing right
                    # away, so the user gets the error message at the right place.
                    if more is None:
                        break
                else:
                    self.input_hist_raw.append("\n")
            # final newline in case the input didn't have it, so that the code
            # actually does get executed
            if more:
                self.push_line('\n')

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

        # if the source code has leading blanks, add 'if 1:\n' to it
        # this allows execution of indented pasted code. It is tempting
        # to add '\n' at the end of source to run commands like ' a=1'
        # directly, but this fails for more complicated scenarios
        source=source.encode(self.stdin_encoding)
        if source[:1] in [' ', '\t']:
            source = 'if 1:\n%s' % source

        try:
            code = self.compile(source,filename,symbol)
        except (OverflowError, SyntaxError, ValueError, TypeError, MemoryError):
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
                self.hooks.pre_runcode_hook()
                exec code_obj in self.user_global_ns, self.user_ns
            finally:
                # Reset our crash handler in place
                sys.excepthook = old_excepthook
        except SystemExit:
            self.resetbuffer()
            self.showtraceback()
            warn("Type %exit or %quit to exit IPython "
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
        
    def push_line(self, line):
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
        for subline in line.splitlines():
            self.autoindent_update(subline)
        self.buffer.append(line)
        more = self.runsource('\n'.join(self.buffer), self.filename)
        if not more:
            self.resetbuffer()
        return more

    def split_user_input(self, line):
        # This is really a hold-over to support ipapi and some extensions
        return prefilter.splitUserInput(line)

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

        # Code run by the user may have modified the readline completer state.
        # We must ensure that our completer is back in place.
        if self.has_readline:
            self.set_completer()
        
        try:
            line = raw_input_original(prompt).decode(self.stdin_encoding)
        except ValueError:
            warn("\n********\nYou or a %run:ed script called sys.stdin.close()"
                 " or sys.stdout.close()!\nExiting IPython!")
            self.ask_exit()
            return ""

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
                if self.has_readline: # and some config option is set?
                    try:
                        histlen = self.readline.get_current_history_length()
                        if histlen > 1:
                            newhist = self.input_hist_raw[-1].rstrip()
                            self.readline.remove_history_item(histlen-1)
                            self.readline.replace_history_item(histlen-2,
                                            newhist.encode(self.stdin_encoding))
                    except AttributeError:
                        pass # re{move,place}_history_item are new in 2.4.                
            else:
                self.input_hist_raw.append('%s\n' % line)                
            # only entries starting at first column go to shadow history
            if line.lstrip() == line:
                self.shadowhist.add(line.strip())
        elif not continue_prompt:
            self.input_hist_raw.append('\n')
        try:
            lineout = self.prefilter(line,continue_prompt)
        except:
            # blanket except, in case a user-defined prefilter crashes, so it
            # can't take all of ipython with it.
            self.showtraceback()
            return ''
        else:
            return lineout

    def _prefilter(self, line, continue_prompt):
        """Calls different preprocessors, depending on the form of line."""

        # All handlers *must* return a value, even if it's blank ('').

        # Lines are NOT logged here. Handlers should process the line as
        # needed, update the cache AND log it (so that the input cache array
        # stays synced).

        #.....................................................................
        # Code begins

        #if line.startswith('%crash'): raise RuntimeError,'Crash now!'  # dbg

        # save the line away in case we crash, so the post-mortem handler can
        # record it
        self._last_input_line = line

        #print '***line: <%s>' % line # dbg

        if not line:
            # Return immediately on purely empty lines, so that if the user
            # previously typed some whitespace that started a continuation
            # prompt, he can break out of that loop with just an empty line.
            # This is how the default python prompt works.

            # Only return if the accumulated input buffer was just whitespace!
            if ''.join(self.buffer).isspace():
                self.buffer[:] = []
            return ''
        
        line_info = prefilter.LineInfo(line, continue_prompt)
        
        # the input history needs to track even empty lines
        stripped = line.strip()
        
        if not stripped:
            if not continue_prompt:
                self.outputcache.prompt_count -= 1
            return self.handle_normal(line_info)

        # print '***cont',continue_prompt  # dbg
        # special handlers are only allowed for single line statements
        if continue_prompt and not self.multi_line_specials:
            return self.handle_normal(line_info)


        # See whether any pre-existing handler can take care of it  
        rewritten = self.hooks.input_prefilter(stripped)
        if rewritten != stripped: # ok, some prefilter did something
            rewritten = line_info.pre + rewritten  # add indentation
            return self.handle_normal(prefilter.LineInfo(rewritten,
                                                         continue_prompt))
            
        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg
        
        return prefilter.prefilter(line_info, self)


    def _prefilter_dumb(self, line, continue_prompt):
        """simple prefilter function, for debugging"""
        return self.handle_normal(line,continue_prompt)

    
    def multiline_prefilter(self, line, continue_prompt):
        """ Run _prefilter for each line of input
        
        Covers cases where there are multiple lines in the user entry,
        which is the case when the user goes back to a multiline history
        entry and presses enter.
        
        """
        out = []
        for l in line.rstrip('\n').split('\n'):
            out.append(self._prefilter(l, continue_prompt))
        return '\n'.join(out)
    
    # Set the default prefilter() function (this can be user-overridden)
    prefilter = multiline_prefilter

    def handle_normal(self,line_info):
        """Handle normal input lines. Use as a template for handlers."""

        # With autoindent on, we need some way to exit the input loop, and I
        # don't want to force the user to have to backspace all the way to
        # clear the line.  The rule will be in this case, that either two
        # lines of pure whitespace in a row, or a line of pure whitespace but
        # of a size different to the indent level, will exit the input loop.
        line = line_info.line
        continue_prompt = line_info.continue_prompt
        
        if (continue_prompt and self.autoindent and line.isspace() and
            (0 < abs(len(line) - self.indent_current_nsp) <= 2 or
             (self.buffer[-1]).isspace() )):
            line = ''

        self.log(line,line,continue_prompt)
        return line

    def handle_alias(self,line_info):
        """Handle alias input lines. """
        tgt = self.alias_table[line_info.iFun]
        # print "=>",tgt #dbg
        if callable(tgt):
            if '$' in line_info.line:
                call_meth = '(_ip, _ip.var_expand(%s))'
            else:
                call_meth = '(_ip,%s)'
            line_out = ("%s_sh.%s" + call_meth) % (line_info.preWhitespace,
                                         line_info.iFun, 
            make_quoted_expr(line_info.line))
        else:
            transformed = self.expand_aliases(line_info.iFun,line_info.theRest)

            # pre is needed, because it carries the leading whitespace.  Otherwise
            # aliases won't work in indented sections.
            line_out = '%s_ip.system(%s)' % (line_info.preWhitespace,
                                             make_quoted_expr( transformed ))
        
        self.log(line_info.line,line_out,line_info.continue_prompt)
        #print 'line out:',line_out # dbg
        return line_out

    def handle_shell_escape(self, line_info):
        """Execute the line in a shell, empty return value"""
        #print 'line in :', `line` # dbg
        line = line_info.line
        if line.lstrip().startswith('!!'):
            # rewrite LineInfo's line, iFun and theRest to properly hold the
            # call to %sx and the actual command to be executed, so
            # handle_magic can work correctly.  Note that this works even if
            # the line is indented, so it handles multi_line_specials
            # properly.
            new_rest = line.lstrip()[2:]
            line_info.line = '%ssx %s' % (self.ESC_MAGIC,new_rest)
            line_info.iFun = 'sx'
            line_info.theRest = new_rest
            return self.handle_magic(line_info)
        else:
            cmd = line.lstrip().lstrip('!')
            line_out = '%s_ip.system(%s)' % (line_info.preWhitespace,
                                             make_quoted_expr(cmd))
        # update cache/log and return
        self.log(line,line_out,line_info.continue_prompt)
        return line_out

    def handle_magic(self, line_info):
        """Execute magic functions."""
        iFun    = line_info.iFun
        theRest = line_info.theRest
        cmd = '%s_ip.magic(%s)' % (line_info.preWhitespace,
                                   make_quoted_expr(iFun + " " + theRest))
        self.log(line_info.line,cmd,line_info.continue_prompt)
        #print 'in handle_magic, cmd=<%s>' % cmd  # dbg
        return cmd

    def handle_auto(self, line_info):
        """Hande lines which can be auto-executed, quoting if requested."""

        line    = line_info.line
        iFun    = line_info.iFun
        theRest = line_info.theRest
        pre     = line_info.pre
        continue_prompt = line_info.continue_prompt
        obj = line_info.ofind(self)['obj']

        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg

        # This should only be active for single-line input!
        if continue_prompt:
            self.log(line,line,continue_prompt)
            return line

        force_auto = isinstance(obj, IPyAutocall)
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
            if not theRest and (self.autocall < 2) and not force_auto:
                newcmd = '%s %s' % (iFun,theRest)
                auto_rewrite = False
            else:
                if not force_auto and theRest.startswith('['):
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
            rw = self.outputcache.prompt1.auto_rewrite() + newcmd
            
            try:
                # plain ascii works better w/ pyreadline, on some machines, so
                # we use it and only print uncolored rewrite if we have unicode
                rw = str(rw)
                print >>Term.cout, rw
            except UnicodeEncodeError:
                print "-------------->" + newcmd
            
        # log what is now valid Python, not the actual user input (without the
        # final newline)
        self.log(line,newcmd,continue_prompt)
        return newcmd

    def handle_help(self, line_info):
        """Try to get some help for the object.

        obj? or ?obj   -> basic information.
        obj?? or ??obj -> more details.
        """
        
        line = line_info.line
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
            self.log(line,'#?'+line,line_info.continue_prompt)
            if line:
                #print 'line:<%r>' % line  # dbg
                self.magic_pinfo(line)
            else:
                page(self.usage,screen_lines=self.usable_screen_length)
            return '' # Empty string is needed here!
        except:
            # Pass any other exceptions through to the normal handler
            return self.handle_normal(line_info)
        else:
            # If the code compiles ok, we should handle it normally
            return self.handle_normal(line_info)

    def handle_emacs(self, line_info):
        """Handle input lines marked by python-mode."""

        # Currently, nothing is done.  Later more functionality can be added
        # here if needed.

        # The input cache shouldn't be updated
        return line_info.line
    
    def var_expand(self,cmd,depth=0):
        """Expand python variables in a string.

        The depth argument indicates how many frames above the caller should
        be walked to look for the local namespace where to expand variables.

        The global namespace for expansion is always the user's interactive
        namespace.
        """

        return str(ItplNS(cmd,
                          self.user_ns,  # globals
                          # Skip our own frame in searching for locals:
                          sys._getframe(depth+1).f_locals # locals
                          ))

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

    def ask_exit(self):
        """ Call for exiting. Can be overiden and used as a callback. """
        self.exit_now = True

    def exit(self):
        """Handle interactive exit.

        This method calls the ask_exit callback."""
        if self.confirm_exit:
            if self.ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                self.ask_exit()
        else:
            self.ask_exit()

    def safe_execfile(self,fname,*where,**kw):
        """A safe version of the builtin execfile().

        This version will never throw an exception, and knows how to handle
        ipython logs as well.

        :Parameters:
          fname : string
            Name of the file to be executed.
            
          where : tuple
            One or two namespaces, passed to execfile() as (globals,locals).
            If only one is given, it is passed as both.

        :Keywords:
          islog : boolean (False)

          quiet : boolean (True)

          exit_ignore : boolean (False)
          """

        def syspath_cleanup():
            """Internal cleanup routine for sys.path."""
            if add_dname:
                try:
                    sys.path.remove(dname)
                except ValueError:
                    # For some reason the user has already removed it, ignore.
                    pass
        
        fname = os.path.expanduser(fname)

        # Find things also in current directory.  This is needed to mimic the
        # behavior of running a script from the system command line, where
        # Python inserts the script's directory into sys.path
        dname = os.path.dirname(os.path.abspath(fname))
        add_dname = False
        if dname not in sys.path:
            sys.path.insert(0,dname)
            add_dname = True

        try:
            xfile = open(fname)
        except:
            print >> Term.cerr, \
                  'Could not open file <%s> for safe execution.' % fname
            syspath_cleanup()
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
                if sys.platform == 'win32' and sys.version_info < (2,5,1):
                    # Work around a bug in Python for Windows.  The bug was
                    # fixed in in Python 2.5 r54159 and 54158, but that's still
                    # SVN Python as of March/07.  For details, see:
                    # http://projects.scipy.org/ipython/ipython/ticket/123
                    try:
                        globs,locs = where[0:2]
                    except:
                        try:
                            globs = locs = where[0]
                        except:
                            globs = locs = globals()
                    exec file(fname) in globs,locs
                else:
                    execfile(fname,*where)
            except SyntaxError:
                self.showsyntaxerror()
                warn('Failure executing file: <%s>' % fname)
            except SystemExit,status:
                # Code that correctly sets the exit status flag to success (0)
                # shouldn't be bothered with a traceback.  Note that a plain
                # sys.exit() does NOT set the message to 0 (it's empty) so that
                # will still get a traceback.  Note that the structure of the
                # SystemExit exception changed between Python 2.4 and 2.5, so
                # the checks must be done in a version-dependent way.
                show = False

                if sys.version_info[:2] > (2,5):
                    if status.message!=0 and not kw['exit_ignore']:
                        show = True
                else:
                    if status.code and not kw['exit_ignore']:
                        show = True
                if show:
                    self.showtraceback()
                    warn('Failure executing file: <%s>' % fname)
            except:
                self.showtraceback()
                warn('Failure executing file: <%s>' % fname)

        syspath_cleanup()

#************************* end of file <iplib.py> *****************************
