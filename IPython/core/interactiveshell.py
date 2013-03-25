# -*- coding: utf-8 -*-
"""Main IPython class."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de>
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import print_function

import __builtin__ as builtin_mod
import __future__
import abc
import ast
import atexit
import os
import re
import runpy
import sys
import tempfile
import types
from io import open as io_open

from IPython.config.configurable import SingletonConfigurable
from IPython.core import debugger, oinspect
from IPython.core import magic
from IPython.core import page
from IPython.core import prefilter
from IPython.core import shadowns
from IPython.core import ultratb
from IPython.core.alias import AliasManager, AliasError
from IPython.core.autocall import ExitAutocall
from IPython.core.builtin_trap import BuiltinTrap
from IPython.core.compilerop import CachingCompiler, check_linecache_ipython
from IPython.core.display_trap import DisplayTrap
from IPython.core.displayhook import DisplayHook
from IPython.core.displaypub import DisplayPublisher
from IPython.core.error import UsageError
from IPython.core.extensions import ExtensionManager
from IPython.core.fakemodule import FakeModule, init_fakemod_dict
from IPython.core.formatters import DisplayFormatter
from IPython.core.history import HistoryManager
from IPython.core.inputsplitter import IPythonInputSplitter, ESC_MAGIC, ESC_MAGIC2
from IPython.core.logger import Logger
from IPython.core.macro import Macro
from IPython.core.payload import PayloadManager
from IPython.core.prefilter import PrefilterManager
from IPython.core.profiledir import ProfileDir
from IPython.core.pylabtools import pylab_activate
from IPython.core.prompts import PromptManager
from IPython.lib.latextools import LaTeXTool
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import PyColorize
from IPython.utils import io
from IPython.utils import py3compat
from IPython.utils import openpy
from IPython.utils.decorators import undoc
from IPython.utils.doctestreload import doctest_reload
from IPython.utils.io import ask_yes_no
from IPython.utils.ipstruct import Struct
from IPython.utils.path import get_home_dir, get_ipython_dir, get_py_filename, unquote_filename
from IPython.utils.pickleshare import PickleShareDB
from IPython.utils.process import system, getoutput
from IPython.utils.strdispatch import StrDispatch
from IPython.utils.syspathcontext import prepended_to_syspath
from IPython.utils.text import (format_screen, LSString, SList,
                                DollarFormatter)
from IPython.utils.traitlets import (Integer, CBool, CaselessStrEnum, Enum,
                                     List, Unicode, Instance, Type)
from IPython.utils.warn import warn, error
import IPython.core.hooks

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# compiled regexps for autoindent management
dedent_re = re.compile(r'^\s+raise|^\s+return|^\s+pass')

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

@undoc
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

@undoc
def no_op(*a, **kw): pass

@undoc
class NoOpContext(object):
    def __enter__(self): pass
    def __exit__(self, type, value, traceback): pass
no_op_context = NoOpContext()

class SpaceInInput(Exception): pass

@undoc
class Bunch: pass


def get_default_colors():
    if sys.platform=='darwin':
        return "LightBG"
    elif os.name=='nt':
        return 'Linux'
    else:
        return 'Linux'


class SeparateUnicode(Unicode):
    """A Unicode subclass to validate separate_in, separate_out, etc.

    This is a Unicode based trait that converts '0'->'' and '\\n'->'\n'.
    """

    def validate(self, obj, value):
        if value == '0': value = ''
        value = value.replace('\\n','\n')
        return super(SeparateUnicode, self).validate(obj, value)


class ReadlineNoRecord(object):
    """Context manager to execute some code, then reload readline history
    so that interactive input to the code doesn't appear when pressing up."""
    def __init__(self, shell):
        self.shell = shell
        self._nested_level = 0

    def __enter__(self):
        if self._nested_level == 0:
            try:
                self.orig_length = self.current_length()
                self.readline_tail = self.get_readline_tail()
            except (AttributeError, IndexError):   # Can fail with pyreadline
                self.orig_length, self.readline_tail = 999999, []
        self._nested_level += 1

    def __exit__(self, type, value, traceback):
        self._nested_level -= 1
        if self._nested_level == 0:
            # Try clipping the end if it's got longer
            try:
                e = self.current_length() - self.orig_length
                if e > 0:
                    for _ in range(e):
                        self.shell.readline.remove_history_item(self.orig_length)

                # If it still doesn't match, just reload readline history.
                if self.current_length() != self.orig_length \
                    or self.get_readline_tail() != self.readline_tail:
                    self.shell.refill_readline_hist()
            except (AttributeError, IndexError):
                pass
        # Returning False will cause exceptions to propagate
        return False

    def current_length(self):
        return self.shell.readline.get_current_history_length()

    def get_readline_tail(self, n=10):
        """Get the last n items in readline history."""
        end = self.shell.readline.get_current_history_length() + 1
        start = max(end-n, 1)
        ghi = self.shell.readline.get_history_item
        return [ghi(x) for x in range(start, end)]

#-----------------------------------------------------------------------------
# Main IPython class
#-----------------------------------------------------------------------------

class InteractiveShell(SingletonConfigurable):
    """An enhanced, interactive shell for Python."""

    _instance = None
    
    ast_transformers = List([], config=True, help=
        """
        A list of ast.NodeTransformer subclass instances, which will be applied
        to user input before code is run.
        """
    )

    autocall = Enum((0,1,2), default_value=0, config=True, help=
        """
        Make IPython automatically call any callable object even if you didn't
        type explicit parentheses. For example, 'str 43' becomes 'str(43)'
        automatically. The value can be '0' to disable the feature, '1' for
        'smart' autocall, where it is not applied if there are no more
        arguments on the line, and '2' for 'full' autocall, where all callable
        objects are automatically called (even if no arguments are present).
        """
    )
    # TODO: remove all autoindent logic and put into frontends.
    # We can't do this yet because even runlines uses the autoindent.
    autoindent = CBool(True, config=True, help=
        """
        Autoindent IPython code entered interactively.
        """
    )
    automagic = CBool(True, config=True, help=
        """
        Enable magic commands to be called without the leading %.
        """
    )
    cache_size = Integer(1000, config=True, help=
        """
        Set the size of the output cache.  The default is 1000, you can
        change it permanently in your config file.  Setting it to 0 completely
        disables the caching system, and the minimum value accepted is 20 (if
        you provide a value less than 20, it is reset to 0 and a warning is
        issued).  This limit is defined because otherwise you'll spend more
        time re-flushing a too small cache than working
        """
    )
    color_info = CBool(True, config=True, help=
        """
        Use colors for displaying information about objects. Because this
        information is passed through a pager (like 'less'), and some pagers
        get confused with color codes, this capability can be turned off.
        """
    )
    colors = CaselessStrEnum(('NoColor','LightBG','Linux'),
                             default_value=get_default_colors(), config=True,
        help="Set the color scheme (NoColor, Linux, or LightBG)."
    )
    colors_force = CBool(False, help=
        """
        Force use of ANSI color codes, regardless of OS and readline
        availability.
        """
        # FIXME: This is essentially a hack to allow ZMQShell to show colors
        # without readline on Win32. When the ZMQ formatting system is
        # refactored, this should be removed.
    )
    debug = CBool(False, config=True)
    deep_reload = CBool(False, config=True, help=
        """
        Enable deep (recursive) reloading by default. IPython can use the
        deep_reload module which reloads changes in modules recursively (it
        replaces the reload() function, so you don't need to change anything to
        use it). deep_reload() forces a full reload of modules whose code may
        have changed, which the default reload() function does not.  When
        deep_reload is off, IPython will use the normal reload(), but
        deep_reload will still be available as dreload().
        """
    )
    disable_failing_post_execute = CBool(False, config=True,
        help="Don't call post-execute functions that have failed in the past."
    )
    display_formatter = Instance(DisplayFormatter)
    displayhook_class = Type(DisplayHook)
    display_pub_class = Type(DisplayPublisher)
    data_pub_class = None

    exit_now = CBool(False)
    exiter = Instance(ExitAutocall)
    def _exiter_default(self):
        return ExitAutocall(self)
    # Monotonically increasing execution counter
    execution_count = Integer(1)
    filename = Unicode("<ipython console>")
    ipython_dir= Unicode('', config=True) # Set to get_ipython_dir() in __init__

    # Input splitter, to split entire cells of input into either individual
    # interactive statements or whole blocks.
    input_splitter = Instance('IPython.core.inputsplitter.IPythonInputSplitter',
                              (), {})
    logstart = CBool(False, config=True, help=
        """
        Start logging to the default log file.
        """
    )
    logfile = Unicode('', config=True, help=
        """
        The name of the logfile to use.
        """
    )
    logappend = Unicode('', config=True, help=
        """
        Start logging to the given file in append mode.
        """
    )
    object_info_string_level = Enum((0,1,2), default_value=0,
                                    config=True)
    pdb = CBool(False, config=True, help=
        """
        Automatically call the pdb debugger after every exception.
        """
    )
    multiline_history = CBool(sys.platform != 'win32', config=True,
        help="Save multi-line entries as one entry in readline history"
    )

    # deprecated prompt traits:
    
    prompt_in1 = Unicode('In [\\#]: ', config=True,
        help="Deprecated, use PromptManager.in_template")
    prompt_in2 = Unicode('   .\\D.: ', config=True,
        help="Deprecated, use PromptManager.in2_template")
    prompt_out = Unicode('Out[\\#]: ', config=True,
        help="Deprecated, use PromptManager.out_template")
    prompts_pad_left = CBool(True, config=True,
        help="Deprecated, use PromptManager.justify")
    
    def _prompt_trait_changed(self, name, old, new):
        table = {
            'prompt_in1' : 'in_template',
            'prompt_in2' : 'in2_template',
            'prompt_out' : 'out_template',
            'prompts_pad_left' : 'justify',
        }
        warn("InteractiveShell.{name} is deprecated, use PromptManager.{newname}".format(
                name=name, newname=table[name])
        )
        # protect against weird cases where self.config may not exist:
        if self.config is not None:
            # propagate to corresponding PromptManager trait
            setattr(self.config.PromptManager, table[name], new)
    
    _prompt_in1_changed = _prompt_trait_changed
    _prompt_in2_changed = _prompt_trait_changed
    _prompt_out_changed = _prompt_trait_changed
    _prompt_pad_left_changed = _prompt_trait_changed
    
    show_rewritten_input = CBool(True, config=True,
        help="Show rewritten input, e.g. for autocall."
    )
    
    quiet = CBool(False, config=True)

    history_length = Integer(10000, config=True)

    # The readline stuff will eventually be moved to the terminal subclass
    # but for now, we can't do that as readline is welded in everywhere.
    readline_use = CBool(True, config=True)
    readline_remove_delims = Unicode('-/~', config=True)
    readline_delims = Unicode() # set by init_readline()
    # don't use \M- bindings by default, because they
    # conflict with 8-bit encodings. See gh-58,gh-88
    readline_parse_and_bind = List([
            'tab: complete',
            '"\C-l": clear-screen',
            'set show-all-if-ambiguous on',
            '"\C-o": tab-insert',
            '"\C-r": reverse-search-history',
            '"\C-s": forward-search-history',
            '"\C-p": history-search-backward',
            '"\C-n": history-search-forward',
            '"\e[A": history-search-backward',
            '"\e[B": history-search-forward',
            '"\C-k": kill-line',
            '"\C-u": unix-line-discard',
        ], allow_none=False, config=True)

    ast_node_interactivity = Enum(['all', 'last', 'last_expr', 'none'],
                                  default_value='last_expr', config=True, 
                                  help="""
        'all', 'last', 'last_expr' or 'none', specifying which nodes should be
        run interactively (displaying output from expressions).""")

    # TODO: this part of prompt management should be moved to the frontends.
    # Use custom TraitTypes that convert '0'->'' and '\\n'->'\n'
    separate_in = SeparateUnicode('\n', config=True)
    separate_out = SeparateUnicode('', config=True)
    separate_out2 = SeparateUnicode('', config=True)
    wildcards_case_sensitive = CBool(True, config=True)
    xmode = CaselessStrEnum(('Context','Plain', 'Verbose'),
                            default_value='Context', config=True)

    # Subcomponents of InteractiveShell
    alias_manager = Instance('IPython.core.alias.AliasManager')
    prefilter_manager = Instance('IPython.core.prefilter.PrefilterManager')
    builtin_trap = Instance('IPython.core.builtin_trap.BuiltinTrap')
    display_trap = Instance('IPython.core.display_trap.DisplayTrap')
    extension_manager = Instance('IPython.core.extensions.ExtensionManager')
    payload_manager = Instance('IPython.core.payload.PayloadManager')
    history_manager = Instance('IPython.core.history.HistoryManager')
    magics_manager = Instance('IPython.core.magic.MagicsManager')

    profile_dir = Instance('IPython.core.application.ProfileDir')
    @property
    def profile(self):
        if self.profile_dir is not None:
            name = os.path.basename(self.profile_dir.location)
            return name.replace('profile_','')


    # Private interface
    _post_execute = Instance(dict)

    # Tracks any GUI loop loaded for pylab
    pylab_gui_select = None

    def __init__(self, config=None, ipython_dir=None, profile_dir=None,
                 user_module=None, user_ns=None,
                 custom_exceptions=((), None)):

        # This is where traits with a config_key argument are updated
        # from the values on config.
        super(InteractiveShell, self).__init__(config=config)
        self.configurables = [self]

        # These are relatively independent and stateless
        self.init_ipython_dir(ipython_dir)
        self.init_profile_dir(profile_dir)
        self.init_instance_attrs()
        self.init_environment()
        
        # Check if we're in a virtualenv, and set up sys.path.
        self.init_virtualenv()

        # Create namespaces (user_ns, user_global_ns, etc.)
        self.init_create_namespaces(user_module, user_ns)
        # This has to be done after init_create_namespaces because it uses
        # something in self.user_ns, but before init_sys_modules, which
        # is the first thing to modify sys.
        # TODO: When we override sys.stdout and sys.stderr before this class
        # is created, we are saving the overridden ones here. Not sure if this
        # is what we want to do.
        self.save_sys_module_state()
        self.init_sys_modules()

        # While we're trying to have each part of the code directly access what
        # it needs without keeping redundant references to objects, we have too
        # much legacy code that expects ip.db to exist.
        self.db = PickleShareDB(os.path.join(self.profile_dir.location, 'db'))

        self.init_history()
        self.init_encoding()
        self.init_prefilter()

        self.init_syntax_highlighting()
        self.init_hooks()
        self.init_pushd_popd_magic()
        # self.init_traceback_handlers use to be here, but we moved it below
        # because it and init_io have to come after init_readline.
        self.init_user_ns()
        self.init_logger()
        self.init_alias()
        self.init_builtins()

        # The following was in post_config_initialization
        self.init_inspector()
        # init_readline() must come before init_io(), because init_io uses
        # readline related things.
        self.init_readline()
        # We save this here in case user code replaces raw_input, but it needs
        # to be after init_readline(), because PyPy's readline works by replacing
        # raw_input.
        if py3compat.PY3:
            self.raw_input_original = input
        else:
            self.raw_input_original = raw_input
        # init_completer must come after init_readline, because it needs to
        # know whether readline is present or not system-wide to configure the
        # completers, since the completion machinery can now operate
        # independently of readline (e.g. over the network)
        self.init_completer()
        # TODO: init_io() needs to happen before init_traceback handlers
        # because the traceback handlers hardcode the stdout/stderr streams.
        # This logic in in debugger.Pdb and should eventually be changed.
        self.init_io()
        self.init_traceback_handlers(custom_exceptions)
        self.init_prompts()
        self.init_display_formatter()
        self.init_display_pub()
        self.init_data_pub()
        self.init_displayhook()
        self.init_reload_doctest()
        self.init_latextool()
        self.init_magics()
        self.init_logstart()
        self.init_pdb()
        self.init_extension_manager()
        self.init_payload()
        self.hooks.late_startup_hook()
        atexit.register(self.atexit_operations)

    def get_ipython(self):
        """Return the currently running IPython instance."""
        return self

    #-------------------------------------------------------------------------
    # Trait changed handlers
    #-------------------------------------------------------------------------

    def _ipython_dir_changed(self, name, new):
        if not os.path.isdir(new):
            os.makedirs(new, mode = 0o777)

    def set_autoindent(self,value=None):
        """Set the autoindent flag, checking for readline support.

        If called with no arguments, it acts as a toggle."""

        if value != 0 and not self.has_readline:
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
            return

        self.ipython_dir = get_ipython_dir()

    def init_profile_dir(self, profile_dir):
        if profile_dir is not None:
            self.profile_dir = profile_dir
            return
        self.profile_dir =\
            ProfileDir.create_profile_dir_by_name(self.ipython_dir, 'default')

    def init_instance_attrs(self):
        self.more = False

        # command compiler
        self.compile = CachingCompiler()

        # Make an empty namespace, which extension writers can rely on both
        # existing and NEVER being used by ipython itself.  This gives them a
        # convenient location for storing additional information and state
        # their extensions may require, without fear of collisions with other
        # ipython names that may develop later.
        self.meta = Struct()

        # Temporary files used for various purposes.  Deleted at exit.
        self.tempfiles = []

        # Keep track of readline usage (later set by init_readline)
        self.has_readline = False

        # keep track of where we started running (mainly for crash post-mortem)
        # This is not being used anywhere currently.
        self.starting_dir = os.getcwdu()

        # Indentation management
        self.indent_current_nsp = 0

        # Dict to track post-execution functions that have been registered
        self._post_execute = {}

    def init_environment(self):
        """Any changes we need to make to the user's environment."""
        pass

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
        self.home_dir = get_home_dir()

        self.dir_stack = []

    def init_logger(self):
        self.logger = Logger(self.home_dir, logfname='ipython_log.py',
                             logmode='rotate')

    def init_logstart(self):
        """Initialize logging in case it was requested at the command line.
        """
        if self.logappend:
            self.magic('logstart %s append' % self.logappend)
        elif self.logfile:
            self.magic('logstart %s' % self.logfile)
        elif self.logstart:
            self.magic('logstart')

    def init_builtins(self):
        # A single, static flag that we set to True.  Its presence indicates
        # that an IPython shell has been created, and we make no attempts at
        # removing on exit or representing the existence of more than one
        # IPython at a time.
        builtin_mod.__dict__['__IPYTHON__'] = True

        # In 0.11 we introduced '__IPYTHON__active' as an integer we'd try to
        # manage on enter/exit, but with all our shells it's virtually
        # impossible to get all the cases right.  We're leaving the name in for
        # those who adapted their codes to check for this flag, but will
        # eventually remove it after a few more releases.
        builtin_mod.__dict__['__IPYTHON__active'] = \
                                          'Deprecated, check for __IPYTHON__'

        self.builtin_trap = BuiltinTrap(shell=self)

    def init_inspector(self):
        # Object inspector
        self.inspector = oinspect.Inspector(oinspect.InspectColors,
                                            PyColorize.ANSICodeColors,
                                            'NoColor',
                                            self.object_info_string_level)

    def init_io(self):
        # This will just use sys.stdout and sys.stderr. If you want to
        # override sys.stdout and sys.stderr themselves, you need to do that
        # *before* instantiating this class, because io holds onto
        # references to the underlying streams.
        if (sys.platform == 'win32' or sys.platform == 'cli') and self.has_readline:
            io.stdout = io.stderr = io.IOStream(self.readline._outputfile)
        else:
            io.stdout = io.IOStream(sys.stdout)
            io.stderr = io.IOStream(sys.stderr)

    def init_prompts(self):
        self.prompt_manager = PromptManager(shell=self, config=self.config)
        self.configurables.append(self.prompt_manager)
        # Set system prompts, so that scripts can decide if they are running
        # interactively.
        sys.ps1 = 'In : '
        sys.ps2 = '...: '
        sys.ps3 = 'Out: '

    def init_display_formatter(self):
        self.display_formatter = DisplayFormatter(config=self.config)
        self.configurables.append(self.display_formatter)

    def init_display_pub(self):
        self.display_pub = self.display_pub_class(config=self.config)
        self.configurables.append(self.display_pub)

    def init_data_pub(self):
        if not self.data_pub_class:
            self.data_pub = None
            return
        self.data_pub = self.data_pub_class(config=self.config)
        self.configurables.append(self.data_pub)

    def init_displayhook(self):
        # Initialize displayhook, set in/out prompts and printing system
        self.displayhook = self.displayhook_class(
            config=self.config,
            shell=self,
            cache_size=self.cache_size,
        )
        self.configurables.append(self.displayhook)
        # This is a context manager that installs/revmoes the displayhook at
        # the appropriate time.
        self.display_trap = DisplayTrap(hook=self.displayhook)

    def init_reload_doctest(self):
        # Do a proper resetting of doctest, including the necessary displayhook
        # monkeypatching
        try:
            doctest_reload()
        except ImportError:
            warn("doctest module does not exist.")

    def init_latextool(self):
        """Configure LaTeXTool."""
        cfg = LaTeXTool.instance(config=self.config)
        if cfg not in self.configurables:
            self.configurables.append(cfg)

    def init_virtualenv(self):
        """Add a virtualenv to sys.path so the user can import modules from it.
        This isn't perfect: it doesn't use the Python interpreter with which the
        virtualenv was built, and it ignores the --no-site-packages option. A
        warning will appear suggesting the user installs IPython in the
        virtualenv, but for many cases, it probably works well enough.
        
        Adapted from code snippets online.
        
        http://blog.ufsoft.org/2009/1/29/ipython-and-virtualenv
        """
        if 'VIRTUAL_ENV' not in os.environ:
            # Not in a virtualenv
            return
        
        if sys.executable.startswith(os.environ['VIRTUAL_ENV']):
            # Running properly in the virtualenv, don't need to do anything
            return
        
        warn("Attempting to work in a virtualenv. If you encounter problems, please "
             "install IPython inside the virtualenv.")
        if sys.platform == "win32":
            virtual_env = os.path.join(os.environ['VIRTUAL_ENV'], 'Lib', 'site-packages') 
        else:
            virtual_env = os.path.join(os.environ['VIRTUAL_ENV'], 'lib',
                       'python%d.%d' % sys.version_info[:2], 'site-packages')
        
        import site
        sys.path.insert(0, virtual_env)
        site.addsitedir(virtual_env)

    #-------------------------------------------------------------------------
    # Things related to injections into the sys module
    #-------------------------------------------------------------------------

    def save_sys_module_state(self):
        """Save the state of hooks in the sys module.

        This has to be called after self.user_module is created.
        """
        self._orig_sys_module_state = {}
        self._orig_sys_module_state['stdin'] = sys.stdin
        self._orig_sys_module_state['stdout'] = sys.stdout
        self._orig_sys_module_state['stderr'] = sys.stderr
        self._orig_sys_module_state['excepthook'] = sys.excepthook
        self._orig_sys_modules_main_name = self.user_module.__name__
        self._orig_sys_modules_main_mod = sys.modules.get(self.user_module.__name__)

    def restore_sys_module_state(self):
        """Restore the state of the sys module."""
        try:
            for k, v in self._orig_sys_module_state.iteritems():
                setattr(sys, k, v)
        except AttributeError:
            pass
        # Reset what what done in self.init_sys_modules
        if self._orig_sys_modules_main_mod is not None:
            sys.modules[self._orig_sys_modules_main_name] = self._orig_sys_modules_main_mod

    #-------------------------------------------------------------------------
    # Things related to hooks
    #-------------------------------------------------------------------------

    def init_hooks(self):
        # hooks holds pointers used for user-side customizations
        self.hooks = Struct()

        self.strdispatchers = {}

        # Set all default hooks, defined in the IPython.hooks module.
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

        f = types.MethodType(hook,self)

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
            print("Warning! Hook '%s' is not one of %s" % \
                  (name, IPython.core.hooks.__all__ ))
        if not dp:
            dp = IPython.core.hooks.CommandChainDispatcher()

        try:
            dp.add(f,priority)
        except AttributeError:
            # it was not commandchain, plain old func - replace
            dp = f

        setattr(self.hooks,name, dp)

    def register_post_execute(self, func):
        """Register a function for calling after code execution.
        """
        if not callable(func):
            raise ValueError('argument %s must be callable' % func)
        self._post_execute[func] = True
    
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
            raise ValueError('new call_pdb value must be boolean')

        # store value in instance
        self._call_pdb = val

        # notify the actual exception handlers
        self.InteractiveTB.call_pdb = val

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

        with self.readline_no_record:
            pm()

    #-------------------------------------------------------------------------
    # Things related to IPython's various namespaces
    #-------------------------------------------------------------------------
    default_user_namespaces = True

    def init_create_namespaces(self, user_module=None, user_ns=None):
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

        # These routines return a properly built module and dict as needed by
        # the rest of the code, and can also be used by extension writers to
        # generate properly initialized namespaces.
        if (user_ns is not None) or (user_module is not None):
            self.default_user_namespaces = False
        self.user_module, self.user_ns = self.prepare_user_module(user_module, user_ns)

        # A record of hidden variables we have added to the user namespace, so
        # we can list later only variables defined in actual interactive use.
        self.user_ns_hidden = set()

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
        self.ns_table = {'user_global':self.user_module.__dict__,
                         'user_local':self.user_ns,
                         'builtin':builtin_mod.__dict__
                         }
    
    @property
    def user_global_ns(self):
        return self.user_module.__dict__

    def prepare_user_module(self, user_module=None, user_ns=None):
        """Prepare the module and namespace in which user code will be run.
        
        When IPython is started normally, both parameters are None: a new module
        is created automatically, and its __dict__ used as the namespace.
        
        If only user_module is provided, its __dict__ is used as the namespace.
        If only user_ns is provided, a dummy module is created, and user_ns
        becomes the global namespace. If both are provided (as they may be
        when embedding), user_ns is the local namespace, and user_module
        provides the global namespace.

        Parameters
        ----------
        user_module : module, optional
            The current user module in which IPython is being run. If None,
            a clean module will be created.
        user_ns : dict, optional
            A namespace in which to run interactive commands.

        Returns
        -------
        A tuple of user_module and user_ns, each properly initialised.
        """
        if user_module is None and user_ns is not None:
            user_ns.setdefault("__name__", "__main__")
            class DummyMod(object):
                "A dummy module used for IPython's interactive namespace."
                pass
            user_module = DummyMod()
            user_module.__dict__ = user_ns
            
        if user_module is None:
            user_module = types.ModuleType("__main__",
                doc="Automatically created module for IPython interactive environment")
        
        # We must ensure that __builtin__ (without the final 's') is always
        # available and pointing to the __builtin__ *module*.  For more details:
        # http://mail.python.org/pipermail/python-dev/2001-April/014068.html
        user_module.__dict__.setdefault('__builtin__', builtin_mod)
        user_module.__dict__.setdefault('__builtins__', builtin_mod)
        
        if user_ns is None:
            user_ns = user_module.__dict__

        return user_module, user_ns

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
        main_name = self.user_module.__name__
        sys.modules[main_name] = self.user_module

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
        # user_ns, and we sync that contents into user_ns_hidden so that these
        # initial variables aren't shown by %who.  After the sync, we add the
        # rest of what we *do* want the user to see with %who even on a new
        # session (probably nothing, so theye really only see their own stuff)

        # The user dict must *always* have a __builtin__ reference to the
        # Python standard __builtin__ namespace,  which must be imported.
        # This is so that certain operations in prompt evaluation can be
        # reliably executed with builtins.  Note that we can NOT use
        # __builtins__ (note the 's'),  because that can either be a dict or a
        # module, and can even mutate at runtime, depending on the context
        # (Python makes no guarantees on it).  In contrast, __builtin__ is
        # always a module object, though it must be explicitly imported.

        # For more details:
        # http://mail.python.org/pipermail/python-dev/2001-April/014068.html
        ns = dict()
        
        # Put 'help' in the user namespace
        try:
            from site import _Helper
            ns['help'] = _Helper()
        except ImportError:
            warn('help() not available - check site.py')

        # make global variables for user access to the histories
        ns['_ih'] = self.history_manager.input_hist_parsed
        ns['_oh'] = self.history_manager.output_hist
        ns['_dh'] = self.history_manager.dir_hist

        ns['_sh'] = shadowns

        # user aliases to input and output histories.  These shouldn't show up
        # in %who, as they can have very large reprs.
        ns['In']  = self.history_manager.input_hist_parsed
        ns['Out'] = self.history_manager.output_hist

        # Store myself as the public api!!!
        ns['get_ipython'] = self.get_ipython
        
        ns['exit'] = self.exiter
        ns['quit'] = self.exiter

        # Sync what we've added so far to user_ns_hidden so these aren't seen
        # by %who
        self.user_ns_hidden.update(ns)

        # Anything put into ns now would show up in %who.  Think twice before
        # putting anything here, as we really want %who to show the user their
        # stuff, not our variables.

        # Finally, update the real user's namespace
        self.user_ns.update(ns)
    
    @property
    def all_ns_refs(self):
        """Get a list of references to all the namespace dictionaries in which
        IPython might store a user-created object.
        
        Note that this does not include the displayhook, which also caches
        objects from the output."""
        return [self.user_ns, self.user_global_ns,
                self._user_main_module.__dict__] + self._main_ns_cache.values()

    def reset(self, new_session=True):
        """Clear all internal namespaces, and attempt to release references to
        user objects.

        If new_session is True, a new history session will be opened.
        """
        # Clear histories
        self.history_manager.reset(new_session)
        # Reset counter used to index all histories
        if new_session:
            self.execution_count = 1

        # Flush cached output items
        if self.displayhook.do_full_cache:
            self.displayhook.flush()

        # The main execution namespaces must be cleared very carefully,
        # skipping the deletion of the builtin-related keys, because doing so
        # would cause errors in many object's __del__ methods.
        if self.user_ns is not self.user_global_ns:
            self.user_ns.clear()
        ns = self.user_global_ns
        drop_keys = set(ns.keys())
        drop_keys.discard('__builtin__')
        drop_keys.discard('__builtins__')
        drop_keys.discard('__name__')
        for k in drop_keys:
            del ns[k]
        
        self.user_ns_hidden.clear()
        
        # Restore the user namespaces to minimal usability
        self.init_user_ns()

        # Restore the default and user aliases
        self.alias_manager.clear_aliases()
        self.alias_manager.init_aliases()

        # Flush the private list of module references kept for script
        # execution protection
        self.clear_main_mod_cache()

        # Clear out the namespace from the last %run
        self.new_main_mod()

    def del_var(self, varname, by_name=False):
        """Delete a variable from the various namespaces, so that, as
        far as possible, we're not keeping any hidden references to it.

        Parameters
        ----------
        varname : str
            The name of the variable to delete.
        by_name : bool
            If True, delete variables with the given name in each
            namespace. If False (default), find the variable in the user
            namespace, and delete references to it.
        """
        if varname in ('__builtin__', '__builtins__'):
            raise ValueError("Refusing to delete %s" % varname)

        ns_refs = self.all_ns_refs
        
        if by_name:                    # Delete by name
            for ns in ns_refs:
                try:
                    del ns[varname]
                except KeyError:
                    pass
        else:                         # Delete by object
            try:
                obj = self.user_ns[varname]
            except KeyError:
                raise NameError("name '%s' is not defined" % varname)
            # Also check in output history
            ns_refs.append(self.history_manager.output_hist)
            for ns in ns_refs:
                to_delete = [n for n, o in ns.iteritems() if o is obj]
                for name in to_delete:
                    del ns[name]

            # displayhook keeps extra references, but not in a dictionary
            for name in ('_', '__', '___'):
                if getattr(self.displayhook, name) is obj:
                    setattr(self.displayhook, name, None)

    def reset_selective(self, regex=None):
        """Clear selective variables from internal namespaces based on a
        specified regular expression.

        Parameters
        ----------
        regex : string or compiled pattern, optional
            A regular expression pattern that will be used in searching
            variable names in the users namespaces.
        """
        if regex is not None:
            try:
                m = re.compile(regex)
            except TypeError:
                raise TypeError('regex must be a string or compiled pattern')
            # Search for keys in each namespace that match the given regex
            # If a match is found, delete the key/value pair.
            for ns in self.all_ns_refs:
                for var in ns:
                    if m.search(var):
                        del ns[var]

    def push(self, variables, interactive=True):
        """Inject a group of variables into the IPython user namespace.

        Parameters
        ----------
        variables : dict, str or list/tuple of str
            The variables to inject into the user's namespace.  If a dict, a
            simple update is done.  If a str, the string is assumed to have
            variable names separated by spaces.  A list/tuple of str can also
            be used to give the variable names.  If just the variable names are
            give (list/tuple/str) then the variable values looked up in the
            callers frame.
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
                    print('Could not get variable %s from %s' %
                           (name,cf.f_code.co_name))
        else:
            raise ValueError('variables must be a dict/str/list/tuple')

        # Propagate variables to user namespace
        self.user_ns.update(vdict)

        # And configure interactive visibility
        user_ns_hidden = self.user_ns_hidden
        if interactive:
            user_ns_hidden.difference_update(vdict)
        else:
            user_ns_hidden.update(vdict)
    
    def drop_by_id(self, variables):
        """Remove a dict of variables from the user namespace, if they are the
        same as the values in the dictionary.
        
        This is intended for use by extensions: variables that they've added can
        be taken back out if they are unloaded, without removing any that the
        user has overwritten.
        
        Parameters
        ----------
        variables : dict
          A dictionary mapping object names (as strings) to the objects.
        """
        for name, obj in variables.iteritems():
            if name in self.user_ns and self.user_ns[name] is obj:
                del self.user_ns[name]
                self.user_ns_hidden.discard(name)

    #-------------------------------------------------------------------------
    # Things related to object introspection
    #-------------------------------------------------------------------------

    def _ofind(self, oname, namespaces=None):
        """Find an object in the available namespaces.

        self._ofind(oname) -> dict with keys: found,obj,ospace,ismagic

        Has special code to detect magic functions.
        """
        oname = oname.strip()
        #print '1- oname: <%r>' % oname  # dbg
        if not oname.startswith(ESC_MAGIC) and \
            not oname.startswith(ESC_MAGIC2) and \
            not py3compat.isidentifier(oname, dotted=True):
            return dict(found=False)

        alias_ns = None
        if namespaces is None:
            # Namespaces to search in:
            # Put them in a list. The order is important so that we
            # find things in the same order that Python finds them.
            namespaces = [ ('Interactive', self.user_ns),
                           ('Interactive (global)', self.user_global_ns),
                           ('Python builtin', builtin_mod.__dict__),
                           ('Alias', self.alias_manager.alias_table),
                           ]
            alias_ns = self.alias_manager.alias_table

        # initialize results to 'null'
        found = False; obj = None;  ospace = None;  ds = None;
        ismagic = False; isalias = False; parent = None

        # We need to special-case 'print', which as of python2.6 registers as a
        # function but should only be treated as one if print_function was
        # loaded with a future import.  In this case, just bail.
        if (oname == 'print' and not py3compat.PY3 and not \
            (self.compile.compiler_flags & __future__.CO_FUTURE_PRINT_FUNCTION)):
            return {'found':found, 'obj':obj, 'namespace':ospace,
                    'ismagic':ismagic, 'isalias':isalias, 'parent':parent}

        # Look for the given name by splitting it in parts.  If the head is
        # found, then we look for all the remaining parts as members, and only
        # declare success if we can find them all.
        oname_parts = oname.split('.')
        oname_head, oname_rest = oname_parts[0],oname_parts[1:]
        for nsname,ns in namespaces:
            try:
                obj = ns[oname_head]
            except KeyError:
                continue
            else:
                #print 'oname_rest:', oname_rest  # dbg
                for part in oname_rest:
                    try:
                        parent = obj
                        obj = getattr(obj,part)
                    except:
                        # Blanket except b/c some badly implemented objects
                        # allow __getattr__ to raise exceptions other than
                        # AttributeError, which then crashes IPython.
                        break
                else:
                    # If we finish the for loop (no break), we got all members
                    found = True
                    ospace = nsname
                    if ns == alias_ns:
                        isalias = True
                    break  # namespace loop

        # Try to see if it's magic
        if not found:
            obj = None
            if oname.startswith(ESC_MAGIC2):
                oname = oname.lstrip(ESC_MAGIC2)
                obj = self.find_cell_magic(oname)
            elif oname.startswith(ESC_MAGIC):
                oname = oname.lstrip(ESC_MAGIC)
                obj = self.find_line_magic(oname)
            else:
                # search without prefix, so run? will find %run?
                obj = self.find_line_magic(oname)
                if obj is None:
                    obj = self.find_cell_magic(oname)
            if obj is not None:
                found = True
                ospace = 'IPython internal'
                ismagic = True

        # Last try: special-case some literals like '', [], {}, etc:
        if not found and oname_head in ["''",'""','[]','{}','()']:
            obj = eval(oname_head)
            found = True
            ospace = 'Interactive'

        return {'found':found, 'obj':obj, 'namespace':ospace,
                'ismagic':ismagic, 'isalias':isalias, 'parent':parent}

    def _ofind_property(self, oname, info):
        """Second part of object finding, to look for property details."""
        if info.found:
            # Get the docstring of the class property if it exists.
            path = oname.split('.')
            root = '.'.join(path[:-1])
            if info.parent is not None:
                try:
                    target = getattr(info.parent, '__class__')
                    # The object belongs to a class instance.
                    try:
                        target = getattr(target, path[-1])
                        # The class defines the object.
                        if isinstance(target, property):
                            oname = root + '.__class__.' + path[-1]
                            info = Struct(self._ofind(oname))
                    except AttributeError: pass
                except AttributeError: pass

        # We return either the new info or the unmodified input if the object
        # hadn't been found
        return info

    def _object_find(self, oname, namespaces=None):
        """Find an object and return a struct with info about it."""
        inf = Struct(self._ofind(oname, namespaces))
        return Struct(self._ofind_property(oname, inf))

    def _inspect(self, meth, oname, namespaces=None, **kw):
        """Generic interface to the inspector system.

        This function is meant to be called by pdef, pdoc & friends."""
        info = self._object_find(oname, namespaces)
        if info.found:
            pmethod = getattr(self.inspector, meth)
            formatter = format_screen if info.ismagic else None
            if meth == 'pdoc':
                pmethod(info.obj, oname, formatter)
            elif meth == 'pinfo':
                pmethod(info.obj, oname, formatter, info, **kw)
            else:
                pmethod(info.obj, oname)
        else:
            print('Object `%s` not found.' % oname)
            return 'not found'  # so callers can take other action

    def object_inspect(self, oname, detail_level=0):
        with self.builtin_trap:
            info = self._object_find(oname)
            if info.found:
                return self.inspector.info(info.obj, oname, info=info,
                            detail_level=detail_level
                )
            else:
                return oinspect.object_info(name=oname, found=False)

    #-------------------------------------------------------------------------
    # Things related to history management
    #-------------------------------------------------------------------------

    def init_history(self):
        """Sets up the command history, and starts regular autosaves."""
        self.history_manager = HistoryManager(shell=self, config=self.config)
        self.configurables.append(self.history_manager)

    #-------------------------------------------------------------------------
    # Things related to exception handling and tracebacks (not debugging)
    #-------------------------------------------------------------------------

    def init_traceback_handlers(self, custom_exceptions):
        # Syntax error handler.
        self.SyntaxTB = ultratb.SyntaxTB(color_scheme='NoColor')

        # The interactive one is initialized with an offset, meaning we always
        # want to remove the topmost item in the traceback, which is our own
        # internal code. Valid modes: ['Plain','Context','Verbose']
        self.InteractiveTB = ultratb.AutoFormattedTB(mode = 'Plain',
                                                     color_scheme='NoColor',
                                                     tb_offset = 1,
                                   check_cache=check_linecache_ipython)

        # The instance will store a pointer to the system-wide exception hook,
        # so that runtime code (such as magics) can access it.  This is because
        # during the read-eval loop, it may get temporarily overwritten.
        self.sys_excepthook = sys.excepthook

        # and add any custom exception handlers the user may have specified
        self.set_custom_exc(*custom_exceptions)

        # Set the exception mode
        self.InteractiveTB.set_mode(mode=self.xmode)

    def set_custom_exc(self, exc_tuple, handler):
        """set_custom_exc(exc_tuple,handler)

        Set a custom exception handler, which will be called if any of the
        exceptions in exc_tuple occur in the mainloop (specifically, in the
        run_code() method).

        Parameters
        ----------

        exc_tuple : tuple of exception classes
            A *tuple* of exception classes, for which to call the defined
            handler.  It is very important that you use a tuple, and NOT A
            LIST here, because of the way Python's except statement works.  If
            you only want to trap a single exception, use a singleton tuple::

                exc_tuple == (MyCustomException,)

        handler : callable
            handler must have the following signature::

                def my_handler(self, etype, value, tb, tb_offset=None):
                    ...
                    return structured_traceback

            Your handler must return a structured traceback (a list of strings),
            or None.

            This will be made into an instance method (via types.MethodType)
            of IPython itself, and it will be called if any of the exceptions
            listed in the exc_tuple are caught. If the handler is None, an
            internal basic one is used, which just prints basic info.

            To protect IPython from crashes, if your handler ever raises an
            exception or returns an invalid result, it will be immediately
            disabled.

        WARNING: by putting in your own exception handler into IPython's main
        execution loop, you run a very good chance of nasty crashes.  This
        facility should only be used if you really know what you are doing."""

        assert type(exc_tuple)==type(()) , \
               "The custom exceptions must be given AS A TUPLE."

        def dummy_handler(self,etype,value,tb,tb_offset=None):
            print('*** Simple custom exception handler ***')
            print('Exception type :',etype)
            print('Exception value:',value)
            print('Traceback      :',tb)
            #print 'Source code    :','\n'.join(self.buffer)
        
        def validate_stb(stb):
            """validate structured traceback return type
            
            return type of CustomTB *should* be a list of strings, but allow
            single strings or None, which are harmless.
            
            This function will *always* return a list of strings,
            and will raise a TypeError if stb is inappropriate.
            """
            msg = "CustomTB must return list of strings, not %r" % stb
            if stb is None:
                return []
            elif isinstance(stb, basestring):
                return [stb]
            elif not isinstance(stb, list):
                raise TypeError(msg)
            # it's a list
            for line in stb:
                # check every element
                if not isinstance(line, basestring):
                    raise TypeError(msg)
            return stb

        if handler is None:
            wrapped = dummy_handler
        else:
            def wrapped(self,etype,value,tb,tb_offset=None):
                """wrap CustomTB handler, to protect IPython from user code
                
                This makes it harder (but not impossible) for custom exception
                handlers to crash IPython.
                """
                try:
                    stb = handler(self,etype,value,tb,tb_offset=tb_offset)
                    return validate_stb(stb)
                except:
                    # clear custom handler immediately
                    self.set_custom_exc((), None)
                    print("Custom TB Handler failed, unregistering", file=io.stderr)
                    # show the exception in handler first
                    stb = self.InteractiveTB.structured_traceback(*sys.exc_info())
                    print(self.InteractiveTB.stb2text(stb), file=io.stdout)
                    print("The original exception:", file=io.stdout)
                    stb = self.InteractiveTB.structured_traceback(
                                            (etype,value,tb), tb_offset=tb_offset
                    )
                return stb

        self.CustomTB = types.MethodType(wrapped,self)
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

    def _get_exc_info(self, exc_tuple=None):
        """get exc_info from a given tuple, sys.exc_info() or sys.last_type etc.
        
        Ensures sys.last_type,value,traceback hold the exc_info we found,
        from whichever source.
        
        raises ValueError if none of these contain any information
        """
        if exc_tuple is None:
            etype, value, tb = sys.exc_info()
        else:
            etype, value, tb = exc_tuple

        if etype is None:
            if hasattr(sys, 'last_type'):
                etype, value, tb = sys.last_type, sys.last_value, \
                                   sys.last_traceback
        
        if etype is None:
            raise ValueError("No exception to find")
        
        # Now store the exception info in sys.last_type etc.
        # WARNING: these variables are somewhat deprecated and not
        # necessarily safe to use in a threaded environment, but tools
        # like pdb depend on their existence, so let's set them.  If we
        # find problems in the field, we'll need to revisit their use.
        sys.last_type = etype
        sys.last_value = value
        sys.last_traceback = tb
        
        return etype, value, tb
    

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
            try:
                etype, value, tb = self._get_exc_info(exc_tuple)
            except ValueError:
                self.write_err('No traceback available to show.\n')
                return
            
            if issubclass(etype, SyntaxError):
                # Though this won't be called by syntax errors in the input
                # line, there may be SyntaxError cases with imported code.
                self.showsyntaxerror(filename)
            elif etype is UsageError:
                self.write_err("UsageError: %s" % value)
            else:
                if exception_only:
                    stb = ['An exception has occurred, use %tb to see '
                           'the full traceback.\n']
                    stb.extend(self.InteractiveTB.get_exception_only(etype,
                                                                     value))
                else:
                    try:
                        # Exception classes can customise their traceback - we
                        # use this in IPython.parallel for exceptions occurring
                        # in the engines. This should return a list of strings.
                        stb = value._render_traceback_()
                    except Exception:
                        stb = self.InteractiveTB.structured_traceback(etype,
                                            value, tb, tb_offset=tb_offset)

                    self._showtraceback(etype, value, stb)
                    if self.call_pdb:
                        # drop into debugger
                        self.debugger(force=True)
                    return

                # Actually show the traceback
                self._showtraceback(etype, value, stb)

        except KeyboardInterrupt:
            self.write_err("\nKeyboardInterrupt\n")

    def _showtraceback(self, etype, evalue, stb):
        """Actually show a traceback.

        Subclasses may override this method to put the traceback on a different
        place, like a side channel.
        """
        print(self.InteractiveTB.stb2text(stb), file=io.stdout)

    def showsyntaxerror(self, filename=None):
        """Display the syntax error that just occurred.

        This doesn't display a stack trace because there isn't one.

        If a filename is given, it is stuffed in the exception instead
        of what was there before (because Python's parser always uses
        "<string>" when reading from a string).
        """
        etype, value, last_traceback = self._get_exc_info()

        if filename and issubclass(etype, SyntaxError):
            try:
                value.filename = filename
            except:
                # Not the format we expect; leave it alone
                pass
        
        stb = self.SyntaxTB.structured_traceback(etype, value, [])
        self._showtraceback(etype, value, stb)

    # This is overridden in TerminalInteractiveShell to show a message about
    # the %paste magic.
    def showindentationerror(self):
        """Called by run_cell when there's an IndentationError in code entered
        at the prompt.

        This is overridden in TerminalInteractiveShell to show a message about
        the %paste magic."""
        self.showsyntaxerror()

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
            self.readline_no_record = no_op_context
            self.set_readline_completer = no_op
            self.set_custom_completer = no_op
            if self.readline_use:
                warn('Readline services not available or not loaded.')
        else:
            self.has_readline = True
            self.readline = readline
            sys.modules['readline'] = readline

            # Platform-specific configuration
            if os.name == 'nt':
                # FIXME - check with Frederick to see if we can harmonize
                # naming conventions with pyreadline to avoid this
                # platform-dependent check
                self.readline_startup_hook = readline.set_pre_input_hook
            else:
                self.readline_startup_hook = readline.set_startup_hook

            # Load user's initrc file (readline config)
            # Or if libedit is used, load editrc.
            inputrc_name = os.environ.get('INPUTRC')
            if inputrc_name is None:
                inputrc_name = '.inputrc'
                if readline.uses_libedit:
                    inputrc_name = '.editrc'
                inputrc_name = os.path.join(self.home_dir, inputrc_name)
            if os.path.isfile(inputrc_name):
                try:
                    readline.read_init_file(inputrc_name)
                except:
                    warn('Problems reading readline initialization file <%s>'
                         % inputrc_name)

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
            delims = readline.get_completer_delims()
            if not py3compat.PY3:
                delims = delims.encode("ascii", "ignore")
            for d in self.readline_remove_delims:
                delims = delims.replace(d, "")
            delims = delims.replace(ESC_MAGIC, '')
            readline.set_completer_delims(delims)
            # Store these so we can restore them if something like rpy2 modifies
            # them.
            self.readline_delims = delims
            # otherwise we end up with a monster history after a while:
            readline.set_history_length(self.history_length)

            self.refill_readline_hist()
            self.readline_no_record = ReadlineNoRecord(self)

        # Configure auto-indent for all platforms
        self.set_autoindent(self.autoindent)

    def refill_readline_hist(self):
        # Load the last 1000 lines from history
        self.readline.clear_history()
        stdin_encoding = sys.stdin.encoding or "utf-8"
        last_cell = u""
        for _, _, cell in self.history_manager.get_tail(1000,
                                                        include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                if self.multiline_history:
                      self.readline.add_history(py3compat.unicode_to_str(cell,
                                                                stdin_encoding))
                else:
                    for line in cell.splitlines():
                        self.readline.add_history(py3compat.unicode_to_str(line,
                                                                stdin_encoding))
                last_cell = cell

    @skip_doctest
    def set_next_input(self, s):
        """ Sets the 'default' input string for the next command line.

        Requires readline.

        Example::

            In [1]: _ip.set_next_input("Hello Word")
            In [2]: Hello Word_  # cursor is here
        """
        self.rl_next_input = py3compat.cast_bytes_py2(s)

    # Maybe move this to the terminal subclass?
    def pre_readline(self):
        """readline hook to be used at the start of each line.

        Currently it handles auto-indent only."""

        if self.rl_do_indent:
            self.readline.insert_text(self._indent_current_str())
        if self.rl_next_input is not None:
            self.readline.insert_text(self.rl_next_input)
            self.rl_next_input = None

    def _indent_current_str(self):
        """return the current level of indentation as a string"""
        return self.input_splitter.indent_spaces * ' '

    #-------------------------------------------------------------------------
    # Things related to text completion
    #-------------------------------------------------------------------------

    def init_completer(self):
        """Initialize the completion machinery.

        This creates completion machinery that can be used by client code,
        either interactively in-process (typically triggered by the readline
        library), programatically (such as in test suites) or out-of-prcess
        (typically over the network by remote frontends).
        """
        from IPython.core.completer import IPCompleter
        from IPython.core.completerlib import (module_completer,
                magic_run_completer, cd_completer, reset_completer)

        self.Completer = IPCompleter(shell=self,
                                     namespace=self.user_ns,
                                     global_namespace=self.user_global_ns,
                                     alias_table=self.alias_manager.alias_table,
                                     use_readline=self.has_readline,
                                     config=self.config,
                                     )
        self.configurables.append(self.Completer)

        # Add custom completers to the basic ones built into IPCompleter
        sdisp = self.strdispatchers.get('complete_command', StrDispatch())
        self.strdispatchers['complete_command'] = sdisp
        self.Completer.custom_completers = sdisp

        self.set_hook('complete_command', module_completer, str_key = 'import')
        self.set_hook('complete_command', module_completer, str_key = 'from')
        self.set_hook('complete_command', magic_run_completer, str_key = '%run')
        self.set_hook('complete_command', cd_completer, str_key = '%cd')
        self.set_hook('complete_command', reset_completer, str_key = '%reset')

        # Only configure readline if we truly are using readline.  IPython can
        # do tab-completion over the network, in GUIs, etc, where readline
        # itself may be absent
        if self.has_readline:
            self.set_readline_completer()

    def complete(self, text, line=None, cursor_pos=None):
        """Return the completed text and a list of completions.

        Parameters
        ----------

           text : string
             A string of text to be completed on.  It can be given as empty and
             instead a line/position pair are given.  In this case, the
             completer itself will split the line like readline does.

           line : string, optional
             The complete line that text is part of.

           cursor_pos : int, optional
             The position of the cursor on the input line.

        Returns
        -------
          text : string
            The actual text that was completed.

          matches : list
            A sorted list with all possible completions.

        The optional arguments allow the completion to take more context into
        account, and are part of the low-level completion API.

        This is a wrapper around the completion mechanism, similar to what
        readline does at the command line when the TAB key is hit.  By
        exposing it as a method, it can be used by other non-readline
        environments (such as GUIs) for text completion.

        Simple usage example:

        In [1]: x = 'hello'

        In [2]: _ip.complete('x.l')
        Out[2]: ('x.l', ['x.ljust', 'x.lower', 'x.lstrip'])
        """

        # Inject names into __builtin__ so we can complete on the added names.
        with self.builtin_trap:
            return self.Completer.complete(text, line, cursor_pos)

    def set_custom_completer(self, completer, pos=0):
        """Adds a new custom completer function.

        The position argument (defaults to 0) is the index in the completers
        list where you want the completer to be inserted."""

        newcomp = types.MethodType(completer,self.Completer)
        self.Completer.matchers.insert(pos,newcomp)

    def set_readline_completer(self):
        """Reset readline's completer to be our own."""
        self.readline.set_completer(self.Completer.rlcomplete)

    def set_completer_frame(self, frame=None):
        """Set the frame of the completer."""
        if frame:
            self.Completer.namespace = frame.f_locals
            self.Completer.global_namespace = frame.f_globals
        else:
            self.Completer.namespace = self.user_ns
            self.Completer.global_namespace = self.user_global_ns

    #-------------------------------------------------------------------------
    # Things related to magics
    #-------------------------------------------------------------------------

    def init_magics(self):
        from IPython.core import magics as m
        self.magics_manager = magic.MagicsManager(shell=self,
                                   confg=self.config,
                                   user_magics=m.UserMagics(self))
        self.configurables.append(self.magics_manager)

        # Expose as public API from the magics manager
        self.register_magics = self.magics_manager.register
        self.register_magic_function = self.magics_manager.register_function
        self.define_magic = self.magics_manager.define_magic

        self.register_magics(m.AutoMagics, m.BasicMagics, m.CodeMagics,
            m.ConfigMagics, m.DeprecatedMagics, m.DisplayMagics, m.ExecutionMagics,
            m.ExtensionMagics, m.HistoryMagics, m.LoggingMagics,
            m.NamespaceMagics, m.OSMagics, m.PylabMagics, m.ScriptMagics,
        )

        # Register Magic Aliases
        mman = self.magics_manager
        mman.register_alias('ed', 'edit')
        mman.register_alias('hist', 'history')
        mman.register_alias('rep', 'recall')
        mman.register_alias('SVG', 'svg', 'cell')
        mman.register_alias('HTML', 'html', 'cell')

        # FIXME: Move the color initialization to the DisplayHook, which
        # should be split into a prompt manager and displayhook. We probably
        # even need a centralize colors management object.
        self.magic('colors %s' % self.colors)

    def run_line_magic(self, magic_name, line):
        """Execute the given line magic.

        Parameters
        ----------
        magic_name : str
          Name of the desired magic function, without '%' prefix.

        line : str
          The rest of the input line as a single string.
        """
        fn = self.find_line_magic(magic_name)
        if fn is None:
            cm = self.find_cell_magic(magic_name)
            etpl = "Line magic function `%%%s` not found%s."
            extra = '' if cm is None else (' (But cell magic `%%%%%s` exists, '
                                    'did you mean that instead?)' % magic_name )
            error(etpl % (magic_name, extra))
        else:
            # Note: this is the distance in the stack to the user's frame.
            # This will need to be updated if the internal calling logic gets
            # refactored, or else we'll be expanding the wrong variables.
            stack_depth = 2
            magic_arg_s = self.var_expand(line, stack_depth)
            # Put magic args in a list so we can call with f(*a) syntax
            args = [magic_arg_s]
            kwargs = {}
            # Grab local namespace if we need it:
            if getattr(fn, "needs_local_scope", False):
                kwargs['local_ns'] = sys._getframe(stack_depth).f_locals
            with self.builtin_trap:
                result = fn(*args,**kwargs)
            return result

    def run_cell_magic(self, magic_name, line, cell):
        """Execute the given cell magic.
        
        Parameters
        ----------
        magic_name : str
          Name of the desired magic function, without '%' prefix.

        line : str
          The rest of the first input line as a single string.

        cell : str
          The body of the cell as a (possibly multiline) string.
        """
        fn = self.find_cell_magic(magic_name)
        if fn is None:
            lm = self.find_line_magic(magic_name)
            etpl = "Cell magic function `%%{0}` not found{1}."
            extra = '' if lm is None else (' (But line magic `%{0}` exists, '
                            'did you mean that instead?)'.format(magic_name))
            error(etpl.format(magic_name, extra))
        elif cell == '':
            raise UsageError('%%{0} (with double %) expects code beneath it. '
                            'Did you mean %{0} (single %)?'.format(magic_name))
        else:
            # Note: this is the distance in the stack to the user's frame.
            # This will need to be updated if the internal calling logic gets
            # refactored, or else we'll be expanding the wrong variables.
            stack_depth = 2
            magic_arg_s = self.var_expand(line, stack_depth)
            with self.builtin_trap:
                result = fn(magic_arg_s, cell)
            return result

    def find_line_magic(self, magic_name):
        """Find and return a line magic by name.

        Returns None if the magic isn't found."""
        return self.magics_manager.magics['line'].get(magic_name)

    def find_cell_magic(self, magic_name):
        """Find and return a cell magic by name.

        Returns None if the magic isn't found."""
        return self.magics_manager.magics['cell'].get(magic_name)

    def find_magic(self, magic_name, magic_kind='line'):
        """Find and return a magic of the given type by name.

        Returns None if the magic isn't found."""
        return self.magics_manager.magics[magic_kind].get(magic_name)

    def magic(self, arg_s):
        """DEPRECATED. Use run_line_magic() instead.

        Call a magic function by name.

        Input: a string containing the name of the magic function to call and
        any additional arguments to be passed to the magic.

        magic('name -opt foo bar') is equivalent to typing at the ipython
        prompt:

        In[1]: %name -opt foo bar

        To call a magic without arguments, simply use magic('name').

        This provides a proper Python function to call IPython's magics in any
        valid Python code you can type at the interpreter, including loops and
        compound statements.
        """
        # TODO: should we issue a loud deprecation warning here?
        magic_name, _, magic_arg_s = arg_s.partition(' ')
        magic_name = magic_name.lstrip(prefilter.ESC_MAGIC)
        return self.run_line_magic(magic_name, magic_arg_s)

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

    def system_piped(self, cmd):
        """Call the given cmd in a subprocess, piping stdout/err

        Parameters
        ----------
        cmd : str
          Command to execute (can not end in '&', as background processes are
          not supported.  Should not be a command that expects input
          other than simple text.
        """
        if cmd.rstrip().endswith('&'):
            # this is *far* from a rigorous test
            # We do not support backgrounding processes because we either use
            # pexpect or pipes to read from.  Users can always just call
            # os.system() or use ip.system=ip.system_raw
            # if they really want a background process.
            raise OSError("Background processes not supported.")

        # we explicitly do NOT return the subprocess status code, because
        # a non-None value would trigger :func:`sys.displayhook` calls.
        # Instead, we store the exit_code in user_ns.
        self.user_ns['_exit_code'] = system(self.var_expand(cmd, depth=1))

    def system_raw(self, cmd):
        """Call the given cmd in a subprocess using os.system

        Parameters
        ----------
        cmd : str
          Command to execute.
        """
        cmd = self.var_expand(cmd, depth=1)
        # protect os.system from UNC paths on Windows, which it can't handle:
        if sys.platform == 'win32':
            from IPython.utils._process_win32 import AvoidUNCPath
            with AvoidUNCPath() as path:
                if path is not None:
                    cmd = '"pushd %s &&"%s' % (path, cmd)
                cmd = py3compat.unicode_to_str(cmd)
                ec = os.system(cmd)
        else:
            cmd = py3compat.unicode_to_str(cmd)
            ec = os.system(cmd)
            # The high byte is the exit code, the low byte is a signal number
            # that we discard for now. See the docs for os.wait()
            if ec > 255:
                ec >>= 8
        
        # We explicitly do NOT return the subprocess status code, because
        # a non-None value would trigger :func:`sys.displayhook` calls.
        # Instead, we store the exit_code in user_ns.
        self.user_ns['_exit_code'] = ec

    # use piped system by default, because it is better behaved
    system = system_piped

    def getoutput(self, cmd, split=True, depth=0):
        """Get output (possibly including stderr) from a subprocess.

        Parameters
        ----------
        cmd : str
          Command to execute (can not end in '&', as background processes are
          not supported.
        split : bool, optional
          If True, split the output into an IPython SList.  Otherwise, an
          IPython LSString is returned.  These are objects similar to normal
          lists and strings, with a few convenience attributes for easier
          manipulation of line-based output.  You can use '?' on them for
          details.
        depth : int, optional
          How many frames above the caller are the local variables which should
          be expanded in the command string? The default (0) assumes that the
          expansion variables are in the stack frame calling this function.
        """
        if cmd.rstrip().endswith('&'):
            # this is *far* from a rigorous test
            raise OSError("Background processes not supported.")
        out = getoutput(self.var_expand(cmd, depth=depth+1))
        if split:
            out = SList(out.splitlines())
        else:
            out = LSString(out)
        return out

    #-------------------------------------------------------------------------
    # Things related to aliases
    #-------------------------------------------------------------------------

    def init_alias(self):
        self.alias_manager = AliasManager(shell=self, config=self.config)
        self.configurables.append(self.alias_manager)
        self.ns_table['alias'] = self.alias_manager.alias_table,

    #-------------------------------------------------------------------------
    # Things related to extensions
    #-------------------------------------------------------------------------

    def init_extension_manager(self):
        self.extension_manager = ExtensionManager(shell=self, config=self.config)
        self.configurables.append(self.extension_manager)

    #-------------------------------------------------------------------------
    # Things related to payloads
    #-------------------------------------------------------------------------

    def init_payload(self):
        self.payload_manager = PayloadManager(config=self.config)
        self.configurables.append(self.payload_manager)

    #-------------------------------------------------------------------------
    # Things related to the prefilter
    #-------------------------------------------------------------------------

    def init_prefilter(self):
        self.prefilter_manager = PrefilterManager(shell=self, config=self.config)
        self.configurables.append(self.prefilter_manager)
        # Ultimately this will be refactored in the new interpreter code, but
        # for now, we should expose the main prefilter method (there's legacy
        # code out there that may rely on this).
        self.prefilter = self.prefilter_manager.prefilter_lines

    def auto_rewrite_input(self, cmd):
        """Print to the screen the rewritten form of the user's command.

        This shows visual feedback by rewriting input lines that cause
        automatic calling to kick in, like::

          /f x

        into::

          ------> f(x)

        after the user's input prompt.  This helps the user understand that the
        input line was transformed automatically by IPython.
        """
        if not self.show_rewritten_input:
            return
        
        rw = self.prompt_manager.render('rewrite') + cmd

        try:
            # plain ascii works better w/ pyreadline, on some machines, so
            # we use it and only print uncolored rewrite if we have unicode
            rw = str(rw)
            print(rw, file=io.stdout)
        except UnicodeEncodeError:
            print("------> " + cmd)

    #-------------------------------------------------------------------------
    # Things related to extracting values/expressions from kernel and user_ns
    #-------------------------------------------------------------------------

    def _simple_error(self):
        etype, value = sys.exc_info()[:2]
        return u'[ERROR] {e.__name__}: {v}'.format(e=etype, v=value)

    def user_variables(self, names):
        """Get a list of variable names from the user's namespace.

        Parameters
        ----------
        names : list of strings
          A list of names of variables to be read from the user namespace.

        Returns
        -------
        A dict, keyed by the input names and with the repr() of each value.
        """
        out = {}
        user_ns = self.user_ns
        for varname in names:
            try:
                value = repr(user_ns[varname])
            except:
                value = self._simple_error()
            out[varname] = value
        return out

    def user_expressions(self, expressions):
        """Evaluate a dict of expressions in the user's namespace.

        Parameters
        ----------
        expressions : dict
          A dict with string keys and string values.  The expression values
          should be valid Python expressions, each of which will be evaluated
          in the user namespace.

        Returns
        -------
        A dict, keyed like the input expressions dict, with the repr() of each
        value.
        """
        out = {}
        user_ns = self.user_ns
        global_ns = self.user_global_ns
        for key, expr in expressions.iteritems():
            try:
                value = repr(eval(expr, global_ns, user_ns))
            except:
                value = self._simple_error()
            out[key] = value
        return out

    #-------------------------------------------------------------------------
    # Things related to the running of code
    #-------------------------------------------------------------------------

    def ex(self, cmd):
        """Execute a normal python statement in user namespace."""
        with self.builtin_trap:
            exec cmd in self.user_global_ns, self.user_ns

    def ev(self, expr):
        """Evaluate python expression expr in user namespace.

        Returns the result of evaluation
        """
        with self.builtin_trap:
            return eval(expr, self.user_global_ns, self.user_ns)

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
        raise_exceptions : bool (False)
            If True raise exceptions everywhere. Meant for testing.

        """
        kw.setdefault('exit_ignore', False)
        kw.setdefault('raise_exceptions', False)

        fname = os.path.abspath(os.path.expanduser(fname))

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
                py3compat.execfile(fname,*where)
            except SystemExit as status:
                # If the call was made with 0 or None exit status (sys.exit(0)
                # or sys.exit() ), don't bother showing a traceback, as both of
                # these are considered normal by the OS:
                # > python -c'import sys;sys.exit(0)'; echo $?
                # 0
                # > python -c'import sys;sys.exit()'; echo $?
                # 0
                # For other exit status, we show the exception unless
                # explicitly silenced, but only in short form.
                if kw['raise_exceptions']:
                    raise
                if status.code and not kw['exit_ignore']:
                    self.showtraceback(exception_only=True)
            except:
                if kw['raise_exceptions']:
                    raise
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
                    # self.run_cell currently captures all exceptions
                    # raised in user code.  It would be nice if there were
                    # versions of runlines, execfile that did raise, so
                    # we could catch the errors.
                    self.run_cell(thefile.read(), store_history=False, shell_futures=False)
            except:
                self.showtraceback()
                warn('Unknown failure executing file: <%s>' % fname)

    def safe_run_module(self, mod_name, where):
        """A safe version of runpy.run_module().

        This version will never throw an exception, but instead print
        helpful error messages to the screen.

        `SystemExit` exceptions with status code 0 or None are ignored.

        Parameters
        ----------
        mod_name : string
            The name of the module to be executed.
        where : dict
            The globals namespace.
        """
        try:
            try:
                where.update(
                    runpy.run_module(str(mod_name), run_name="__main__",
                                     alter_sys=True)
                    )
            except SystemExit as status:
                if status.code:
                    raise
        except:
            self.showtraceback()
            warn('Unknown failure executing module: <%s>' % mod_name)

    def _run_cached_cell_magic(self, magic_name, line):
        """Special method to call a cell magic with the data stored in self.
        """
        cell = self._current_cell_magic_body
        self._current_cell_magic_body = None
        return self.run_cell_magic(magic_name, line, cell)

    def run_cell(self, raw_cell, store_history=False, silent=False, shell_futures=True):
        """Run a complete IPython cell.

        Parameters
        ----------
        raw_cell : str
          The code (including IPython code such as %magic functions) to run.
        store_history : bool
          If True, the raw and translated cell will be stored in IPython's
          history. For user code calling back into IPython's machinery, this
          should be set to False.
        silent : bool
          If True, avoid side-effects, such as implicit displayhooks and
          and logging.  silent=True forces store_history=False.
        shell_futures : bool
          If True, the code will share future statements with the interactive
          shell. It will both be affected by previous __future__ imports, and
          any __future__ imports in the code will affect the shell. If False,
          __future__ imports are not shared in either direction.
        """
        if (not raw_cell) or raw_cell.isspace():
            return
        
        if silent:
            store_history = False

        self.input_splitter.push(raw_cell)

        # Check for cell magics, which leave state behind.  This interface is
        # ugly, we need to do something cleaner later...  Now the logic is
        # simply that the input_splitter remembers if there was a cell magic,
        # and in that case we grab the cell body.
        if self.input_splitter.cell_magic_parts:
            self._current_cell_magic_body = \
                               ''.join(self.input_splitter.cell_magic_parts)
        cell = self.input_splitter.source_reset()
        
        # Our own compiler remembers the __future__ environment. If we want to
        # run code with a separate __future__ environment, use the default
        # compiler
        compiler = self.compile if shell_futures else CachingCompiler()

        with self.builtin_trap:
            prefilter_failed = False
            if len(cell.splitlines()) == 1:
                try:
                    # use prefilter_lines to handle trailing newlines
                    # restore trailing newline for ast.parse
                    cell = self.prefilter_manager.prefilter_lines(cell) + '\n'
                except AliasError as e:
                    error(e)
                    prefilter_failed = True
                except Exception:
                    # don't allow prefilter errors to crash IPython
                    self.showtraceback()
                    prefilter_failed = True

            # Store raw and processed history
            if store_history:
                self.history_manager.store_inputs(self.execution_count,
                                                  cell, raw_cell)
            if not silent:
                self.logger.log(cell, raw_cell)

            if not prefilter_failed:
                # don't run if prefilter failed
                cell_name = self.compile.cache(cell, self.execution_count)

                with self.display_trap:
                    try:
                        code_ast = compiler.ast_parse(cell, filename=cell_name)
                    except IndentationError:
                        self.showindentationerror()
                        if store_history:
                            self.execution_count += 1
                        return None
                    except (OverflowError, SyntaxError, ValueError, TypeError,
                            MemoryError):
                        self.showsyntaxerror()
                        if store_history:
                            self.execution_count += 1
                        return None
                    
                    code_ast = self.transform_ast(code_ast)
                    
                    interactivity = "none" if silent else self.ast_node_interactivity
                    self.run_ast_nodes(code_ast.body, cell_name,
                                       interactivity=interactivity, compiler=compiler)
                    
                    # Execute any registered post-execution functions.
                    # unless we are silent
                    post_exec = [] if silent else self._post_execute.iteritems()
                    
                    for func, status in post_exec:
                        if self.disable_failing_post_execute and not status:
                            continue
                        try:
                            func()
                        except KeyboardInterrupt:
                            print("\nKeyboardInterrupt", file=io.stderr)
                        except Exception:
                            # register as failing:
                            self._post_execute[func] = False
                            self.showtraceback()
                            print('\n'.join([
                                "post-execution function %r produced an error." % func,
                                "If this problem persists, you can disable failing post-exec functions with:",
                                "",
                                "    get_ipython().disable_failing_post_execute = True"
                            ]), file=io.stderr)

        if store_history:
            # Write output to the database. Does nothing unless
            # history output logging is enabled.
            self.history_manager.store_output(self.execution_count)
            # Each cell is a *single* input, regardless of how many lines it has
            self.execution_count += 1
    
    def transform_ast(self, node):
        """Apply the AST transformations from self.ast_transformers
        
        Parameters
        ----------
        node : ast.Node
          The root node to be transformed. Typically called with the ast.Module
          produced by parsing user input.
        
        Returns
        -------
        An ast.Node corresponding to the node it was called with. Note that it
        may also modify the passed object, so don't rely on references to the
        original AST.
        """
        for transformer in self.ast_transformers:
            try:
                node = transformer.visit(node)
            except Exception:
                warn("AST transformer %r threw an error. It will be unregistered." % transformer)
                self.ast_transformers.remove(transformer)
        
        if self.ast_transformers:
            ast.fix_missing_locations(node)
        return node
                

    def run_ast_nodes(self, nodelist, cell_name, interactivity='last_expr',
                        compiler=compile):
        """Run a sequence of AST nodes. The execution mode depends on the
        interactivity parameter.

        Parameters
        ----------
        nodelist : list
          A sequence of AST nodes to run.
        cell_name : str
          Will be passed to the compiler as the filename of the cell. Typically
          the value returned by ip.compile.cache(cell).
        interactivity : str
          'all', 'last', 'last_expr' or 'none', specifying which nodes should be
          run interactively (displaying output from expressions). 'last_expr'
          will run the last node interactively only if it is an expression (i.e.
          expressions in loops or other blocks are not displayed. Other values
          for this parameter will raise a ValueError.
        compiler : callable
          A function with the same interface as the built-in compile(), to turn
          the AST nodes into code objects. Default is the built-in compile().
        """
        if not nodelist:
            return

        if interactivity == 'last_expr':
            if isinstance(nodelist[-1], ast.Expr):
                interactivity = "last"
            else:
                interactivity = "none"

        if interactivity == 'none':
            to_run_exec, to_run_interactive = nodelist, []
        elif interactivity == 'last':
            to_run_exec, to_run_interactive = nodelist[:-1], nodelist[-1:]
        elif interactivity == 'all':
            to_run_exec, to_run_interactive = [], nodelist
        else:
            raise ValueError("Interactivity was %r" % interactivity)

        exec_count = self.execution_count

        try:
            for i, node in enumerate(to_run_exec):
                mod = ast.Module([node])
                code = compiler(mod, cell_name, "exec")
                if self.run_code(code):
                    return True

            for i, node in enumerate(to_run_interactive):
                mod = ast.Interactive([node])
                code = compiler(mod, cell_name, "single")
                if self.run_code(code):
                    return True

            # Flush softspace
            if softspace(sys.stdout, 0):
                print()

        except:
            # It's possible to have exceptions raised here, typically by
            # compilation of odd code (such as a naked 'return' outside a
            # function) that did parse but isn't valid. Typically the exception
            # is a SyntaxError, but it's safest just to catch anything and show
            # the user a traceback.

            # We do only one try/except outside the loop to minimize the impact
            # on runtime, and also because if any node in the node list is
            # broken, we should stop execution completely.
            self.showtraceback()

        return False

    def run_code(self, code_obj):
        """Execute a code object.

        When an exception occurs, self.showtraceback() is called to display a
        traceback.

        Parameters
        ----------
        code_obj : code object
          A compiled code object, to be executed

        Returns
        -------
        False : successful execution.
        True : an error occurred.
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
                self.hooks.pre_run_code_hook()
                #rprint('Running code', repr(code_obj)) # dbg
                exec code_obj in self.user_global_ns, self.user_ns
            finally:
                # Reset our crash handler in place
                sys.excepthook = old_excepthook
        except SystemExit:
            self.showtraceback(exception_only=True)
            warn("To exit: use 'exit', 'quit', or Ctrl-D.", level=1)
        except self.custom_exceptions:
            etype,value,tb = sys.exc_info()
            self.CustomTB(etype,value,tb)
        except:
            self.showtraceback()
        else:
            outflag = 0
        return outflag

    # For backwards compatibility
    runcode = run_code

    #-------------------------------------------------------------------------
    # Things related to GUI support and pylab
    #-------------------------------------------------------------------------

    def enable_gui(self, gui=None):
        raise NotImplementedError('Implement enable_gui in a subclass')

    def enable_pylab(self, gui=None, import_all=True, welcome_message=False):
        """Activate pylab support at runtime.

        This turns on support for matplotlib, preloads into the interactive
        namespace all of numpy and pylab, and configures IPython to correctly
        interact with the GUI event loop.  The GUI backend to be used can be
        optionally selected with the optional ``gui`` argument.

        Parameters
        ----------
        gui : optional, string
          If given, dictates the choice of matplotlib GUI backend to use
          (should be one of IPython's supported backends, 'qt', 'osx', 'tk',
          'gtk', 'wx' or 'inline'), otherwise we use the default chosen by
          matplotlib (as dictated by the matplotlib build-time options plus the
          user's matplotlibrc configuration file).  Note that not all backends
          make sense in all contexts, for example a terminal ipython can't
          display figures inline.
        """
        from IPython.core.pylabtools import mpl_runner
        # We want to prevent the loading of pylab to pollute the user's
        # namespace as shown by the %who* magics, so we execute the activation
        # code in an empty namespace, and we update *both* user_ns and
        # user_ns_hidden with this information.
        ns = {}
        try:
            gui = pylab_activate(ns, gui, import_all, self, welcome_message=welcome_message)
        except KeyError:
            error("Backend %r not supported" % gui)
            return
        except ImportError:
            error("pylab mode doesn't work as matplotlib could not be found." + \
                  "\nIs it installed on the system?")
            return
        self.user_ns.update(ns)
        self.user_ns_hidden.update(ns)
        # Now we must activate the gui pylab wants to use, and fix %run to take
        # plot updates into account
        self.enable_gui(gui)
        self.magics_manager.registry['ExecutionMagics'].default_runner = \
        mpl_runner(self.safe_execfile)

    #-------------------------------------------------------------------------
    # Utilities
    #-------------------------------------------------------------------------

    def var_expand(self, cmd, depth=0, formatter=DollarFormatter()):
        """Expand python variables in a string.

        The depth argument indicates how many frames above the caller should
        be walked to look for the local namespace where to expand variables.

        The global namespace for expansion is always the user's interactive
        namespace.
        """
        ns = self.user_ns.copy()
        ns.update(sys._getframe(depth+1).f_locals)
        try:
            # We have to use .vformat() here, because 'self' is a valid and common
            # name, and expanding **ns for .format() would make it collide with
            # the 'self' argument of the method.
            cmd = formatter.vformat(cmd, args=[], kwargs=ns)
        except Exception:
            # if formatter couldn't format, just let it go untransformed
            pass
        return cmd

    def mktempfile(self, data=None, prefix='ipython_edit_'):
        """Make a new tempfile and return its filename.

        This makes a call to tempfile.mktemp, but it registers the created
        filename internally so ipython cleans it up at exit time.

        Optional inputs:

          - data(None): if data is given, it gets written out to the temp file
          immediately, and the file is closed again."""

        filename = tempfile.mktemp('.py', prefix)
        self.tempfiles.append(filename)

        if data:
            tmp_file = open(filename,'w')
            tmp_file.write(data)
            tmp_file.close()
        return filename

    # TODO:  This should be removed when Term is refactored.
    def write(self,data):
        """Write a string to the default output"""
        io.stdout.write(data)

    # TODO:  This should be removed when Term is refactored.
    def write_err(self,data):
        """Write a string to the default error output"""
        io.stderr.write(data)

    def ask_yes_no(self, prompt, default=None):
        if self.quiet:
            return True
        return ask_yes_no(prompt,default)

    def show_usage(self):
        """Show a usage message"""
        page.page(IPython.core.usage.interactive_usage)

    def extract_input_lines(self, range_str, raw=False):
        """Return as a string a set of input history slices.

        Parameters
        ----------
        range_str : string
            The set of slices is given as a string, like "~5/6-~4/2 4:8 9",
            since this function is for use by magic functions which get their
            arguments as strings. The number before the / is the session
            number: ~n goes n back from the current session.

        Optional Parameters:
          - raw(False): by default, the processed input is used.  If this is
          true, the raw input history is used instead.

        Note that slices can be called with two notations:

        N:M -> standard python form, means including items N...(M-1).

        N-M -> include items N..M (closed endpoint)."""
        lines = self.history_manager.get_range_by_str(range_str, raw=raw)
        return "\n".join(x for _, _, x in lines)

    def find_user_code(self, target, raw=True, py_only=False, skip_encoding_cookie=True):
        """Get a code string from history, file, url, or a string or macro.

        This is mainly used by magic functions.

        Parameters
        ----------

        target : str

          A string specifying code to retrieve. This will be tried respectively
          as: ranges of input history (see %history for syntax), url,
          correspnding .py file, filename, or an expression evaluating to a
          string or Macro in the user namespace.

        raw : bool
          If true (default), retrieve raw history. Has no effect on the other
          retrieval mechanisms.

        py_only : bool (default False)
          Only try to fetch python code, do not try alternative methods to decode file
          if unicode fails.

        Returns
        -------
        A string of code.

        ValueError is raised if nothing is found, and TypeError if it evaluates
        to an object of another type. In each case, .args[0] is a printable
        message.
        """
        code = self.extract_input_lines(target, raw=raw)  # Grab history
        if code:
            return code
        utarget = unquote_filename(target)
        try:
            if utarget.startswith(('http://', 'https://')):
                return openpy.read_py_url(utarget, skip_encoding_cookie=skip_encoding_cookie)
        except UnicodeDecodeError:
            if not py_only :
                from urllib import urlopen  # Deferred import
                response = urlopen(target)
                return response.read().decode('latin1')
            raise ValueError(("'%s' seem to be unreadable.") % utarget)

        potential_target = [target]
        try :
            potential_target.insert(0,get_py_filename(target))
        except IOError:
            pass

        for tgt in potential_target :
            if os.path.isfile(tgt):                        # Read file
                try :
                    return openpy.read_py_file(tgt, skip_encoding_cookie=skip_encoding_cookie)
                except UnicodeDecodeError :
                    if not py_only :
                        with io_open(tgt,'r', encoding='latin1') as f :
                            return f.read()
                    raise ValueError(("'%s' seem to be unreadable.") % target)

        try:                                              # User namespace
            codeobj = eval(target, self.user_ns)
        except Exception:
            raise ValueError(("'%s' was not found in history, as a file, url, "
                                "nor in the user namespace.") % target)
        if isinstance(codeobj, basestring):
            return codeobj
        elif isinstance(codeobj, Macro):
            return codeobj.value

        raise TypeError("%s is neither a string nor a macro." % target,
                        codeobj)

    #-------------------------------------------------------------------------
    # Things related to IPython exiting
    #-------------------------------------------------------------------------
    def atexit_operations(self):
        """This will be executed at the time of exit.

        Cleanup operations and saving of persistent data that is done
        unconditionally by IPython should be performed here.

        For things that may depend on startup flags or platform specifics (such
        as having readline or not), register a separate atexit function in the
        code that has the appropriate information, rather than trying to
        clutter
        """
        # Close the history session (this stores the end time and line count)
        # this must be *before* the tempfile cleanup, in case of temporary
        # history db
        self.history_manager.end_session()

        # Cleanup all tempfiles left around
        for tfile in self.tempfiles:
            try:
                os.unlink(tfile)
            except OSError:
                pass

        # Clear all user namespaces to release all references cleanly.
        self.reset(new_session=False)

        # Run user hooks
        self.hooks.shutdown_hook()

    def cleanup(self):
        self.restore_sys_module_state()


class InteractiveShellABC(object):
    """An abstract base class for InteractiveShell."""
    __metaclass__ = abc.ABCMeta

InteractiveShellABC.register(InteractiveShell)
