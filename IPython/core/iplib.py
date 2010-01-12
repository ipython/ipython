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
from __future__ import absolute_import

import __builtin__
import StringIO
import bdb
import codeop
import exceptions
import new
import os
import re
import string
import sys
import tempfile
from contextlib import nested

from IPython.core import debugger, oinspect
from IPython.core import history as ipcorehist
from IPython.core import prefilter
from IPython.core import shadowns
from IPython.core import ultratb
from IPython.core.alias import AliasManager
from IPython.core.builtin_trap import BuiltinTrap
from IPython.core.component import Component
from IPython.core.display_trap import DisplayTrap
from IPython.core.error import TryNext, UsageError
from IPython.core.fakemodule import FakeModule, init_fakemod_dict
from IPython.core.logger import Logger
from IPython.core.magic import Magic
from IPython.core.prefilter import PrefilterManager
from IPython.core.prompts import CachedOutput
from IPython.core.pylabtools import pylab_activate
from IPython.core.usage import interactive_usage, default_banner
from IPython.external.Itpl import ItplNS
from IPython.lib.inputhook import enable_gui
from IPython.lib.backgroundjobs import BackgroundJobManager
from IPython.utils import PyColorize
from IPython.utils import pickleshare
from IPython.utils.genutils import get_ipython_dir
from IPython.utils.ipstruct import Struct
from IPython.utils.platutils import toggle_set_term_title, set_term_title
from IPython.utils.strdispatch import StrDispatch
from IPython.utils.syspathcontext import prepended_to_syspath

# XXX - need to clean up this import * line
from IPython.utils.genutils import *

# from IPython.utils import growl
# growl.start("IPython")

from IPython.utils.traitlets import (
    Int, Str, CBool, CaselessStrEnum, Enum, List, Unicode
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


def no_op(*a, **kw): pass

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


def get_default_colors():
    if sys.platform=='darwin':
        return "LightBG"
    elif os.name=='nt':
        return 'Linux'
    else:
        return 'Linux'


class SeparateStr(Str):
    """A Str subclass to validate separate_in, separate_out, etc.

    This is a Str based traitlet that converts '0'->'' and '\\n'->'\n'.
    """

    def validate(self, obj, value):
        if value == '0': value = ''
        value = value.replace('\\n','\n')
        return super(SeparateStr, self).validate(obj, value)


def make_user_namespaces(user_ns=None, user_global_ns=None):
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

    Parameters
    ----------
    user_ns : dict-like, optional
        The current user namespace. The items in this namespace should
        be included in the output. If None, an appropriate blank
        namespace should be created.
    user_global_ns : dict, optional
        The current user global namespace. The items in this namespace
        should be included in the output. If None, an appropriate
        blank namespace should be created.

    Returns
    -------
        A pair of dictionary-like object to be used as the local namespace
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

#-----------------------------------------------------------------------------
# Main IPython class
#-----------------------------------------------------------------------------


class InteractiveShell(Component, Magic):
    """An enhanced, interactive shell for Python."""

    autocall = Enum((0,1,2), default_value=1, config=True)
    autoedit_syntax = CBool(False, config=True)
    autoindent = CBool(True, config=True)
    automagic = CBool(True, config=True)
    banner = Str('')
    banner1 = Str(default_banner, config=True)
    banner2 = Str('', config=True)
    cache_size = Int(1000, config=True)
    color_info = CBool(True, config=True)
    colors = CaselessStrEnum(('NoColor','LightBG','Linux'), 
                             default_value=get_default_colors(), config=True)
    confirm_exit = CBool(True, config=True)
    debug = CBool(False, config=True)
    deep_reload = CBool(False, config=True)
    # This display_banner only controls whether or not self.show_banner()
    # is called when mainloop/interact are called.  The default is False
    # because for the terminal based application, the banner behavior
    # is controlled by Global.display_banner, which IPythonApp looks at
    # to determine if *it* should call show_banner() by hand or not.
    display_banner = CBool(False) # This isn't configurable!
    embedded = CBool(False)
    embedded_active = CBool(False)
    editor = Str(get_default_editor(), config=True)
    filename = Str("<ipython console>")
    ipython_dir= Unicode('', config=True) # Set to get_ipython_dir() in __init__
    logstart = CBool(False, config=True)
    logfile = Str('', config=True)
    logappend = Str('', config=True)
    object_info_string_level = Enum((0,1,2), default_value=0,
                                    config=True)
    pager = Str('less', config=True)
    pdb = CBool(False, config=True)
    pprint = CBool(True, config=True)
    profile = Str('', config=True)
    prompt_in1 = Str('In [\\#]: ', config=True)
    prompt_in2 = Str('   .\\D.: ', config=True)
    prompt_out = Str('Out[\\#]: ', config=True)
    prompts_pad_left = CBool(True, config=True)
    quiet = CBool(False, config=True)

    readline_use = CBool(True, config=True)
    readline_merge_completions = CBool(True, config=True)
    readline_omit__names = Enum((0,1,2), default_value=0, config=True)
    readline_remove_delims = Str('-/~', config=True)
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
        ], allow_none=False, config=True)

    screen_length = Int(0, config=True)
    
    # Use custom TraitletTypes that convert '0'->'' and '\\n'->'\n'
    separate_in = SeparateStr('\n', config=True)
    separate_out = SeparateStr('', config=True)
    separate_out2 = SeparateStr('', config=True)

    system_header = Str('IPython system call: ', config=True)
    system_verbose = CBool(False, config=True)
    term_title = CBool(False, config=True)
    wildcards_case_sensitive = CBool(True, config=True)
    xmode = CaselessStrEnum(('Context','Plain', 'Verbose'), 
                            default_value='Context', config=True)

    autoexec = List(allow_none=False)

    # class attribute to indicate whether the class supports threads or not.
    # Subclasses with thread support should override this as needed.
    isthreaded = False

    def __init__(self, parent=None, config=None, ipython_dir=None, usage=None,
                 user_ns=None, user_global_ns=None,
                 banner1=None, banner2=None, display_banner=None,
                 custom_exceptions=((),None)):

        # This is where traitlets with a config_key argument are updated
        # from the values on config.
        super(InteractiveShell, self).__init__(parent, config=config)

        # These are relatively independent and stateless
        self.init_ipython_dir(ipython_dir)
        self.init_instance_attrs()
        self.init_term_title()
        self.init_usage(usage)
        self.init_banner(banner1, banner2, display_banner)

        # Create namespaces (user_ns, user_global_ns, etc.)
        self.init_create_namespaces(user_ns, user_global_ns)
        # This has to be done after init_create_namespaces because it uses
        # something in self.user_ns, but before init_sys_modules, which
        # is the first thing to modify sys.
        self.save_sys_module_state()
        self.init_sys_modules()

        self.init_history()
        self.init_encoding()
        self.init_prefilter()

        Magic.__init__(self, self)

        self.init_syntax_highlighting()
        self.init_hooks()
        self.init_pushd_popd_magic()
        self.init_traceback_handlers(custom_exceptions)
        self.init_user_ns()
        self.init_logger()
        self.init_alias()
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

    def get_ipython(self):
        """Return the currently running IPython instance."""
        return self

    #-------------------------------------------------------------------------
    # Traitlet changed handlers
    #-------------------------------------------------------------------------

    def _banner1_changed(self):
        self.compute_banner()

    def _banner2_changed(self):
        self.compute_banner()

    def _ipython_dir_changed(self, name, new):
        if not os.path.isdir(new):
            os.makedirs(new, mode = 0777)
        if not os.path.isdir(self.ipython_extension_dir):
            os.makedirs(self.ipython_extension_dir, mode = 0777)

    @property
    def ipython_extension_dir(self):
        return os.path.join(self.ipython_dir, 'extensions')

    @property
    def usable_screen_length(self):
        if self.screen_length == 0:
            return 0
        else:
            num_lines_bot = self.separate_in.count('\n')+1
            return self.screen_length - num_lines_bot

    def _term_title_changed(self, name, new_value):
        self.init_term_title()

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

    #-------------------------------------------------------------------------
    # init_* methods called by __init__
    #-------------------------------------------------------------------------

    def init_ipython_dir(self, ipython_dir):
        if ipython_dir is not None:
            self.ipython_dir = ipython_dir
            self.config.Global.ipython_dir = self.ipython_dir
            return

        if hasattr(self.config.Global, 'ipython_dir'):
            self.ipython_dir = self.config.Global.ipython_dir
        else:
            self.ipython_dir = get_ipython_dir()

        # All children can just read this
        self.config.Global.ipython_dir = self.ipython_dir

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

    def init_encoding(self):
        # Get system encoding at startup time.  Certain terminals (like Emacs
        # under Win32 have it set to None, and we need to have a known valid
        # encoding to use in the raw_input() method
        try:
            self.stdin_encoding = sys.stdin.encoding or 'ascii'
        except AttributeError:
            self.stdin_encoding = 'ascii'

    def init_syntax_highlighting(self):
        # Python source parser/formatter for syntax highlighting
        pyformat = PyColorize.Parser().format
        self.pycolorize = lambda src: pyformat(src,'str',self.colors)

    def init_pushd_popd_magic(self):
        # for pushd/popd management
        try:
            self.home_dir = get_home_dir()
        except HomeDirError, msg:
            fatal(msg)

        self.dir_stack = []

    def init_logger(self):
        self.logger = Logger(self, logfname='ipython_log.py', logmode='rotate')
        # local shortcut, this is used a LOT
        self.log = self.logger.log

    def init_logstart(self):
        if self.logappend:
            self.magic_logstart(self.logappend + ' append')
        elif self.logfile:
            self.magic_logstart(self.logfile)
        elif self.logstart:
            self.magic_logstart()

    def init_builtins(self):
        self.builtin_trap = BuiltinTrap(self)

    def init_inspector(self):
        # Object inspector
        self.inspector = oinspect.Inspector(oinspect.InspectColors,
                                            PyColorize.ANSICodeColors,
                                            'NoColor',
                                            self.object_info_string_level)

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
        self.display_trap = DisplayTrap(self, self.outputcache)

    def init_reload_doctest(self):
        # Do a proper resetting of doctest, including the necessary displayhook
        # monkeypatching
        try:
            doctest_reload()
        except ImportError:
            warn("doctest module does not exist.")

    #-------------------------------------------------------------------------
    # Things related to the banner
    #-------------------------------------------------------------------------

    def init_banner(self, banner1, banner2, display_banner):
        if banner1 is not None:
            self.banner1 = banner1
        if banner2 is not None:
            self.banner2 = banner2
        if display_banner is not None:
            self.display_banner = display_banner
        self.compute_banner()

    def show_banner(self, banner=None):
        if banner is None:
            banner = self.banner
        self.write(banner)

    def compute_banner(self):
        self.banner = self.banner1 + '\n'
        if self.profile:
            self.banner += '\nIPython profile: %s\n' % self.profile
        if self.banner2:
            self.banner += '\n' + self.banner2 + '\n'

    #-------------------------------------------------------------------------
    # Things related to injections into the sys module
    #-------------------------------------------------------------------------

    def save_sys_module_state(self):
        """Save the state of hooks in the sys module.

        This has to be called after self.user_ns is created.
        """
        self._orig_sys_module_state = {}
        self._orig_sys_module_state['stdin'] = sys.stdin
        self._orig_sys_module_state['stdout'] = sys.stdout
        self._orig_sys_module_state['stderr'] = sys.stderr
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

    #-------------------------------------------------------------------------
    # Things related to hooks
    #-------------------------------------------------------------------------

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

    #-------------------------------------------------------------------------
    # Things related to the "main" module
    #-------------------------------------------------------------------------

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

    #-------------------------------------------------------------------------
    # Things related to debugging
    #-------------------------------------------------------------------------

    def init_pdb(self):
        # Set calling of pdb on exceptions
        # self.call_pdb is a property
        self.call_pdb = self.pdb

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

    #-------------------------------------------------------------------------
    # Things related to IPython's various namespaces
    #-------------------------------------------------------------------------

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
        user_ns, user_global_ns = make_user_namespaces(user_ns, user_global_ns)

        # Assign namespaces
        # This is the namespace where all normal user variables live
        self.user_ns = user_ns
        self.user_global_ns = user_global_ns

        # An auxiliary namespace that checks what parts of the user_ns were
        # loaded at startup, so we can list later only variables defined in
        # actual interactive use.  Since it is always a subset of user_ns, it
        # doesn't need to be separately tracked in the ns_table.
        self.user_config_ns = {}

        # A namespace to keep track of internal data structures to prevent
        # them from cluttering user-visible stuff.  Will be updated later
        self.internal_ns = {}

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
                         'internal':self.internal_ns,
                         'builtin':__builtin__.__dict__
                         }

        # Similarly, track all namespaces where references can be held and that
        # we can safely clear (so it can NOT include builtin).  This one can be
        # a simple list.
        self.ns_refs_table = [ user_ns, user_global_ns, self.user_config_ns,
                               self.internal_ns, self._main_ns_cache ]

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
        # This function works in two parts: first we put a few things in
        # user_ns, and we sync that contents into user_config_ns so that these
        # initial variables aren't shown by %who.  After the sync, we add the
        # rest of what we *do* want the user to see with %who even on a new
        # session.
        ns = {}
        
        # Put 'help' in the user namespace
        try:
            from site import _Helper
            ns['help'] = _Helper()
        except ImportError:
            warn('help() not available - check site.py')

        # make global variables for user access to the histories
        ns['_ih'] = self.input_hist
        ns['_oh'] = self.output_hist
        ns['_dh'] = self.dir_hist

        ns['_sh'] = shadowns

        # Sync what we've added so far to user_config_ns so these aren't seen
        # by %who
        self.user_config_ns.update(ns)

        # Now, continue adding more contents

        # user aliases to input and output histories
        ns['In']  = self.input_hist
        ns['Out'] = self.output_hist

        # Store myself as the public api!!!
        ns['get_ipython'] = self.get_ipython
        
        # And update the real user's namespace
        self.user_ns.update(ns)


    def reset(self):
        """Clear all internal namespaces.

        Note that this is much more aggressive than %reset, since it clears
        fully all namespaces, as well as all input/output lists.
        """
        for ns in self.ns_refs_table:
            ns.clear()

        self.alias_manager.clear_aliases()

        # Clear input and output histories
        self.input_hist[:] = []
        self.input_hist_raw[:] = []
        self.output_hist.clear()

        # Restore the user namespaces to minimal usability
        self.init_user_ns()

        # Restore the default and user aliases
        self.alias_manager.init_aliases()

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

    #-------------------------------------------------------------------------
    # Things related to history management
    #-------------------------------------------------------------------------

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
        if self.profile:
            histfname = 'history-%s' % self.profile
        else:
            histfname = 'history'
        self.histfile = os.path.join(self.ipython_dir, histfname)

        # Fill the history zero entry, user counter starts at 1
        self.input_hist.append('\n')
        self.input_hist_raw.append('\n')

    def init_shadow_hist(self):
        try:
            self.db = pickleshare.PickleShareDB(self.ipython_dir + "/db")
        except exceptions.UnicodeDecodeError:
            print "Your ipython_dir can't be decoded to unicode!"
            print "Please set HOME environment variable to something that"
            print r"only has ASCII characters, e.g. c:\home"
            print "Now it is", self.ipython_dir
            sys.exit()
        self.shadowhist = ipcorehist.ShadowHist(self.db)

    def savehist(self):
        """Save input history to a file (via readline library)."""

        try:
            self.readline.write_history_file(self.histfile)
        except:
            print 'Unable to save IPython command history to file: ' + \
                  `self.histfile`

    def reloadhist(self):
        """Reload the input history from disk file."""

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

    #-------------------------------------------------------------------------
    # Things related to exception handling and tracebacks (not debugging)
    #-------------------------------------------------------------------------

    def init_traceback_handlers(self, custom_exceptions):
        # Syntax error handler.
        self.SyntaxTB = SyntaxTB(color_scheme='NoColor')
        
        # The interactive one is initialized with an offset, meaning we always
        # want to remove the topmost item in the traceback, which is our own
        # internal code. Valid modes: ['Plain','Context','Verbose']
        self.InteractiveTB = ultratb.AutoFormattedTB(mode = 'Plain',
                                                     color_scheme='NoColor',
                                                     tb_offset = 1)

        # The instance will store a pointer to the system-wide exception hook,
        # so that runtime code (such as magics) can access it.  This is because
        # during the read-eval loop, it may get temporarily overwritten.
        self.sys_excepthook = sys.excepthook

        # and add any custom exception handlers the user may have specified
        self.set_custom_exc(*custom_exceptions)

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

    def showtraceback(self,exc_tuple = None,filename=None,tb_offset=None,
                      exception_only=False):
        """Display the exception that just occurred.

        If nothing is known about the exception, this is the method which
        should be used throughout the code for presenting user tracebacks,
        rather than directly invoking the InteractiveTB object.

        A specific showsyntaxerror() also exists, but this method can take
        care of calling it if needed, so unless you are explicitly catching a
        SyntaxError exception, don't try to analyze the stack manually and
        simply call this method."""
        
        try:
            if exc_tuple is None:
                etype, value, tb = sys.exc_info()
            else:
                etype, value, tb = exc_tuple

            if etype is None:
                if hasattr(sys, 'last_type'):
                    etype, value, tb = sys.last_type, sys.last_value, \
                                       sys.last_traceback
                else:
                    self.write('No traceback available to show.\n')
                    return
    
            if etype is SyntaxError:
                # Though this won't be called by syntax errors in the input
                # line, there may be SyntaxError cases whith imported code.
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
                    if exception_only:
                        m = ('An exception has occurred, use %tb to see the '
                             'full traceback.')
                        print m
                        self.InteractiveTB.show_exception_only(etype, value)
                    else:
                        self.InteractiveTB(etype,value,tb,tb_offset=tb_offset)
                        if self.InteractiveTB.call_pdb:
                            # pdb mucks up readline, fix it back
                            self.set_completer()
                        
        except KeyboardInterrupt:
            self.write("\nKeyboardInterrupt\n")        
        

    def showsyntaxerror(self, filename=None):
        """Display the syntax error that just occurred.

        This doesn't display a stack trace because there isn't one.

        If a filename is given, it is stuffed in the exception instead
        of what was there before (because Python's parser always uses
        "<string>" when reading from a string).
        """
        etype, value, last_traceback = sys.exc_info()

        # See note about these variables in showtraceback() above
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
                        # This should be inside a display_trap block and I 
                        # think it is.
                        sys.displayhook(f.read())
                    finally:
                        f.close()
                except:
                    self.showtraceback()

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

    #-------------------------------------------------------------------------
    # Things related to tab completion
    #-------------------------------------------------------------------------

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

    def set_custom_completer(self,completer,pos=0):
        """Adds a new custom completer function.

        The position argument (defaults to 0) is the index in the completers
        list where you want the completer to be inserted."""

        newcomp = new.instancemethod(completer,self.Completer,
                                     self.Completer.__class__)
        self.Completer.matchers.insert(pos,newcomp)

    def set_completer(self):
        """Reset readline's completer to be our own."""
        self.readline.set_completer(self.Completer.complete)

    def set_completer_frame(self, frame=None):
        """Set the frame of the completer."""
        if frame:
            self.Completer.namespace = frame.f_locals
            self.Completer.global_namespace = frame.f_globals
        else:
            self.Completer.namespace = self.user_ns
            self.Completer.global_namespace = self.user_global_ns

    #-------------------------------------------------------------------------
    # Things related to readline
    #-------------------------------------------------------------------------

    def init_readline(self):
        """Command history completion/saving/reloading."""

        if self.readline_use:
            import IPython.utils.rlineimpl as readline
                  
        self.rl_next_input = None
        self.rl_do_indent = False

        if not self.readline_use or not readline.have_readline:
            self.has_readline = False
            self.readline = None
            # Set a number of methods that depend on readline to be no-op
            self.savehist = no_op
            self.reloadhist = no_op
            self.set_completer = no_op
            self.set_custom_completer = no_op
            self.set_completer_frame = no_op
            warn('Readline services not available or not loaded.')
        else:
            self.has_readline = True
            self.readline = readline
            sys.modules['readline'] = readline
            import atexit
            from IPython.core.completer import IPCompleter
            self.Completer = IPCompleter(self,
                                         self.user_ns,
                                         self.user_global_ns,
                                         self.readline_omit__names,
                                         self.alias_manager.alias_table)
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

    def set_next_input(self, s):
        """ Sets the 'default' input string for the next command line.
        
        Requires readline.
        
        Example:
        
        [D:\ipython]|1> _ip.set_next_input("Hello Word")
        [D:\ipython]|2> Hello Word_  # cursor is here        
        """

        self.rl_next_input = s

    def pre_readline(self):
        """readline hook to be used at the start of each line.

        Currently it handles auto-indent only."""

        #debugx('self.indent_current_nsp','pre_readline:')

        if self.rl_do_indent:
            self.readline.insert_text(self._indent_current_str())
        if self.rl_next_input is not None:
            self.readline.insert_text(self.rl_next_input)
            self.rl_next_input = None

    def _indent_current_str(self):
        """return the current level of indentation as a string"""
        return self.indent_current_nsp * ' '

    #-------------------------------------------------------------------------
    # Things related to magics
    #-------------------------------------------------------------------------

    def init_magics(self):
        # Set user colors (don't do it in the constructor above so that it
        # doesn't crash if colors option is invalid)
        self.magic_colors(self.colors)
        # History was moved to a separate module
        from . import history
        history.init_ipython(self)

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
        magic_name = magic_name.lstrip(prefilter.ESC_MAGIC)

        try:
            magic_args = args[1]
        except IndexError:
            magic_args = ''
        fn = getattr(self,'magic_'+magic_name,None)
        if fn is None:
            error("Magic function `%s` not found." % magic_name)
        else:
            magic_args = self.var_expand(magic_args,1)
            with nested(self.builtin_trap,):
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

    #-------------------------------------------------------------------------
    # Things related to macros
    #-------------------------------------------------------------------------

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

    #-------------------------------------------------------------------------
    # Things related to the running of system commands
    #-------------------------------------------------------------------------

    def system(self, cmd):
        """Make a system call, using IPython."""
        return self.hooks.shell_hook(self.var_expand(cmd, depth=2))

    #-------------------------------------------------------------------------
    # Things related to aliases
    #-------------------------------------------------------------------------

    def init_alias(self):
        self.alias_manager = AliasManager(self, config=self.config)
        self.ns_table['alias'] = self.alias_manager.alias_table,

    #-------------------------------------------------------------------------
    # Things related to the running of code
    #-------------------------------------------------------------------------

    def ex(self, cmd):
        """Execute a normal python statement in user namespace."""
        with nested(self.builtin_trap,):
            exec cmd in self.user_global_ns, self.user_ns

    def ev(self, expr):
        """Evaluate python expression expr in user namespace.

        Returns the result of evaluation
        """
        with nested(self.builtin_trap,):
            return eval(expr, self.user_global_ns, self.user_ns)

    def mainloop(self, display_banner=None):
        """Start the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner.
        """
        
        with nested(self.builtin_trap, self.display_trap):

            # if you run stuff with -c <cmd>, raw hist is not updated
            # ensure that it's in sync
            if len(self.input_hist) != len (self.input_hist_raw):
                self.input_hist_raw = InputList(self.input_hist)

            while 1:
                try:
                    self.interact(display_banner=display_banner)
                    #self.interact_with_readline()                
                    # XXX for testing of a readline-decoupled repl loop, call
                    # interact_with_readline above
                    break
                except KeyboardInterrupt:
                    # this should not be necessary, but KeyboardInterrupt
                    # handling seems rather unpredictable...
                    self.write("\nKeyboardInterrupt in interact()\n")

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
        lineout = self.prefilter_manager.prefilter_lines(line,self.more)

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

    def interact(self, display_banner=None):
        """Closely emulate the interactive Python console."""

        # batch run -> do not interact        
        if self.exit_now:
            return

        if display_banner is None:
            display_banner = self.display_banner
        if display_banner:
            self.show_banner()

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
                    if self.has_readline:
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

        # Turn off the exit flag, so the mainloop can be restarted if desired
        self.exit_now = False

    def safe_execfile(self, fname, *where, **kw):
        """A safe version of the builtin execfile().

        This version will never throw an exception, but instead print
        helpful error messages to the screen.  This only works on pure
        Python files with the .py extension.

        Parameters
        ----------
        fname : string
            The name of the file to be executed.
        where : tuple
            One or two namespaces, passed to execfile() as (globals,locals).
            If only one is given, it is passed as both.
        exit_ignore : bool (False)
            If True, then silence SystemExit for non-zero status (it is always
            silenced for zero status, as it is so common).
        """
        kw.setdefault('exit_ignore', False)

        fname = os.path.abspath(os.path.expanduser(fname))

        # Make sure we have a .py file
        if not fname.endswith('.py'):
            warn('File must end with .py to be run using execfile: <%s>' % fname)

        # Make sure we can open the file
        try:
            with open(fname) as thefile:
                pass
        except:
            warn('Could not open file <%s> for safe execution.' % fname)
            return

        # Find things also in current directory.  This is needed to mimic the
        # behavior of running a script from the system command line, where
        # Python inserts the script's directory into sys.path
        dname = os.path.dirname(fname)

        with prepended_to_syspath(dname):
            try:
                execfile(fname,*where)
            except SystemExit, status:
                # If the call was made with 0 or None exit status (sys.exit(0)
                # or sys.exit() ), don't bother showing a traceback, as both of
                # these are considered normal by the OS:
                # > python -c'import sys;sys.exit(0)'; echo $?
                # 0
                # > python -c'import sys;sys.exit()'; echo $?
                # 0
                # For other exit status, we show the exception unless
                # explicitly silenced, but only in short form.
                if status.code not in (0, None) and not kw['exit_ignore']:
                    self.showtraceback(exception_only=True)
            except:
                self.showtraceback()

    def safe_execfile_ipy(self, fname):
        """Like safe_execfile, but for .ipy files with IPython syntax.

        Parameters
        ----------
        fname : str
            The name of the file to execute.  The filename must have a
            .ipy extension.
        """
        fname = os.path.abspath(os.path.expanduser(fname))

        # Make sure we have a .py file
        if not fname.endswith('.ipy'):
            warn('File must end with .py to be run using execfile: <%s>' % fname)

        # Make sure we can open the file
        try:
            with open(fname) as thefile:
                pass
        except:
            warn('Could not open file <%s> for safe execution.' % fname)
            return

        # Find things also in current directory.  This is needed to mimic the
        # behavior of running a script from the system command line, where
        # Python inserts the script's directory into sys.path
        dname = os.path.dirname(fname)

        with prepended_to_syspath(dname):
            try:
                with open(fname) as thefile:
                    script = thefile.read()
                    # self.runlines currently captures all exceptions
                    # raise in user code.  It would be nice if there were
                    # versions of runlines, execfile that did raise, so
                    # we could catch the errors.
                    self.runlines(script, clean=True)
            except:
                self.showtraceback()
                warn('Unknown failure executing file: <%s>' % fname)
                
    def _is_secondary_block_start(self, s):
        if not s.endswith(':'):
            return False
        if (s.startswith('elif') or 
            s.startswith('else') or 
            s.startswith('except') or
            s.startswith('finally')):
            return True

    def cleanup_ipy_script(self, script):
        """Make a script safe for self.runlines()

        Currently, IPython is lines based, with blocks being detected by
        empty lines.  This is a problem for block based scripts that may
        not have empty lines after blocks.  This script adds those empty
        lines to make scripts safe for running in the current line based
        IPython.
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
            if level > 0 and newlevel == 0 and \
                   not self._is_secondary_block_start(stripped): 
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

        with nested(self.builtin_trap, self.display_trap):
            for line in lines:
                # skip blank lines so we don't mess up the prompt counter, but do
                # NOT skip even a blank line if we are in a code block (more is
                # true)
            
                if line or more:
                    # push to raw history, so hist line numbers stay in sync
                    self.input_hist_raw.append("# " + line + "\n")
                    prefiltered = self.prefilter_manager.prefilter_lines(line,more)
                    more = self.push_line(prefiltered)
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
            self.showtraceback(exception_only=True)
            warn("To exit: use any of 'exit', 'quit', %Exit or Ctrl-D.", level=1)
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
            self._autoindent_update(subline)
        self.buffer.append(line)
        more = self.runsource('\n'.join(self.buffer), self.filename)
        if not more:
            self.resetbuffer()
        return more

    def _autoindent_update(self,line):
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
        # growl.notify("raw_input: ", "prompt = %r\ncontinue_prompt = %s" % (prompt, continue_prompt))

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
                if self.has_readline and self.readline_use:
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
            lineout = self.prefilter_manager.prefilter_lines(line,continue_prompt)
        except:
            # blanket except, in case a user-defined prefilter crashes, so it
            # can't take all of ipython with it.
            self.showtraceback()
            return ''
        else:
            return lineout

    #-------------------------------------------------------------------------
    # Working with components
    #-------------------------------------------------------------------------

    def get_component(self, name=None, klass=None):
        """Fetch a component by name and klass in my tree."""
        c = Component.get_instances(root=self, name=name, klass=klass)
        if len(c) == 0:
            return None
        if len(c) == 1:
            return c[0]
        else:
            return c

    #-------------------------------------------------------------------------
    # IPython extensions
    #-------------------------------------------------------------------------

    def load_extension(self, module_str):
        """Load an IPython extension by its module name.

        An IPython extension is an importable Python module that has
        a function with the signature::

            def load_ipython_extension(ipython):
                # Do things with ipython

        This function is called after your extension is imported and the 
        currently active :class:`InteractiveShell` instance is passed as
        the only argument.  You can do anything you want with IPython at
        that point, including defining new magic and aliases, adding new
        components, etc.

        The :func:`load_ipython_extension` will be called again is you 
        load or reload the extension again.  It is up to the extension
        author to add code to manage that.

        You can put your extension modules anywhere you want, as long as
        they can be imported by Python's standard import mechanism.  However,
        to make it easy to write extensions, you can also put your extensions
        in ``os.path.join(self.ipython_dir, 'extensions')``.  This directory
        is added to ``sys.path`` automatically.
        """
        from IPython.utils.syspathcontext import prepended_to_syspath

        if module_str not in sys.modules:
            with prepended_to_syspath(self.ipython_extension_dir):
                __import__(module_str)
        mod = sys.modules[module_str]
        return self._call_load_ipython_extension(mod)

    def unload_extension(self, module_str):
        """Unload an IPython extension by its module name.

        This function looks up the extension's name in ``sys.modules`` and
        simply calls ``mod.unload_ipython_extension(self)``.
        """
        if module_str in sys.modules:
            mod = sys.modules[module_str]
            self._call_unload_ipython_extension(mod)

    def reload_extension(self, module_str):
        """Reload an IPython extension by calling reload.

        If the module has not been loaded before,
        :meth:`InteractiveShell.load_extension` is called. Otherwise
        :func:`reload` is called and then the :func:`load_ipython_extension`
        function of the module, if it exists is called.
        """
        from IPython.utils.syspathcontext import prepended_to_syspath

        with prepended_to_syspath(self.ipython_extension_dir):
            if module_str in sys.modules:
                mod = sys.modules[module_str]
                reload(mod)
                self._call_load_ipython_extension(mod)
            else:
                self.load_extension(module_str)

    def _call_load_ipython_extension(self, mod):
        if hasattr(mod, 'load_ipython_extension'):
            return mod.load_ipython_extension(self)

    def _call_unload_ipython_extension(self, mod):
        if hasattr(mod, 'unload_ipython_extension'):
            return mod.unload_ipython_extension(self)

    #-------------------------------------------------------------------------
    # Things related to the prefilter
    #-------------------------------------------------------------------------

    def init_prefilter(self):
        self.prefilter_manager = PrefilterManager(self, config=self.config)
        # Ultimately this will be refactored in the new interpreter code, but
        # for now, we should expose the main prefilter method (there's legacy
        # code out there that may rely on this).
        self.prefilter = self.prefilter_manager.prefilter_lines

    #-------------------------------------------------------------------------
    # Utilities
    #-------------------------------------------------------------------------

    def getoutput(self, cmd):
        return getoutput(self.var_expand(cmd,depth=2),
                         header=self.system_header,
                         verbose=self.system_verbose)

    def getoutputerror(self, cmd):
        return getoutputerror(self.var_expand(cmd,depth=2),
                              header=self.system_header,
                              verbose=self.system_verbose)

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

    def ask_yes_no(self,prompt,default=True):
        if self.quiet:
            return True
        return ask_yes_no(prompt,default)

    #-------------------------------------------------------------------------
    # Things related to GUI support and pylab
    #-------------------------------------------------------------------------

    def enable_pylab(self, gui=None):
        """Activate pylab support at runtime.

        This turns on support for matplotlib, preloads into the interactive
        namespace all of numpy and pylab, and configures IPython to correcdtly
        interact with the GUI event loop.  The GUI backend to be used can be
        optionally selected with the optional :param:`gui` argument.

        Parameters
        ----------
        gui : optional, string

          If given, dictates the choice of matplotlib GUI backend to use
          (should be one of IPython's supported backends, 'tk', 'qt', 'wx' or
          'gtk'), otherwise we use the default chosen by matplotlib (as
          dictated by the matplotlib build-time options plus the user's
          matplotlibrc configuration file).
        """
        # We want to prevent the loading of pylab to pollute the user's
        # namespace as shown by the %who* magics, so we execute the activation
        # code in an empty namespace, and we update *both* user_ns and
        # user_config_ns with this information.
        ns = {}
        gui = pylab_activate(ns, gui)
        self.user_ns.update(ns)
        self.user_config_ns.update(ns)
        # Now we must activate the gui pylab wants to use, and fix %run to take
        # plot updates into account
        enable_gui(gui)
        self.magic_run = self._pylab_magic_run

    #-------------------------------------------------------------------------
    # Things related to IPython exiting
    #-------------------------------------------------------------------------

    def ask_exit(self):
        """ Ask the shell to exit. Can be overiden and used as a callback. """
        self.exit_now = True

    def exit(self):
        """Handle interactive exit.

        This method calls the ask_exit callback."""
        if self.confirm_exit:
            if self.ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                self.ask_exit()
        else:
            self.ask_exit()

    def atexit_operations(self):
        """This will be executed at the time of exit.

        Saving of persistent data should be performed here.
        """
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

    def cleanup(self):
        self.restore_sys_module_state()


