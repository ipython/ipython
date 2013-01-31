#!/usr/bin/env python
# encoding: utf-8
"""
The :class:`~IPython.core.application.Application` object for the command
line :command:`ipython` program.

Authors
-------

* Brian Granger
* Fernando Perez
* Min Ragan-Kelley
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import absolute_import

import logging
import os
import sys

from IPython.config.loader import (
    Config, PyFileConfigLoader, ConfigFileNotFound
)
from IPython.config.application import boolean_flag, catch_config_error
from IPython.core import release
from IPython.core import usage
from IPython.core.completer import IPCompleter
from IPython.core.crashhandler import CrashHandler
from IPython.core.formatters import PlainTextFormatter
from IPython.core.history import HistoryManager
from IPython.core.prompts import PromptManager
from IPython.core.application import (
    ProfileDir, BaseIPythonApplication, base_flags, base_aliases
)
from IPython.core.magics import ScriptMagics
from IPython.core.shellapp import (
    InteractiveShellApp, shell_flags, shell_aliases
)
from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
from IPython.utils import warn
from IPython.utils.path import get_ipython_dir, check_for_old_config
from IPython.utils.traitlets import (
    Bool, List, Dict, CaselessStrEnum
)

#-----------------------------------------------------------------------------
# Globals, utilities and helpers
#-----------------------------------------------------------------------------

#: The default config file name for this application.
default_config_file_name = u'ipython_config.py'

_examples = """
ipython --pylab            # start in pylab mode
ipython --pylab=qt         # start in pylab mode with the qt4 backend
ipython --log-level=DEBUG  # set logging to DEBUG
ipython --profile=foo      # start with profile foo

ipython qtconsole          # start the qtconsole GUI application
ipython help qtconsole     # show the help for the qtconsole subcmd

ipython console            # start the terminal-based console application
ipython help console       # show the help for the console subcmd

ipython notebook           # start the IPython notebook
ipython help notebook      # show the help for the notebook subcmd

ipython profile create foo # create profile foo w/ default config files
ipython help profile       # show the help for the profile subcmd

ipython locate             # print the path to the IPython directory
ipython locate profile foo # print the path to the directory for profile `foo`
"""

#-----------------------------------------------------------------------------
# Crash handler for this application
#-----------------------------------------------------------------------------

class IPAppCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    def __init__(self, app):
        contact_name = release.author
        contact_email = release.author_email
        bug_tracker = 'https://github.com/ipython/ipython/issues'
        super(IPAppCrashHandler,self).__init__(
            app, contact_name, contact_email, bug_tracker
        )

    def make_report(self,traceback):
        """Return a string containing a crash report."""

        sec_sep = self.section_sep
        # Start with parent report
        report = [super(IPAppCrashHandler, self).make_report(traceback)]
        # Add interactive-specific info we may have
        rpt_add = report.append
        try:
            rpt_add(sec_sep+"History of session input:")
            for line in self.app.shell.user_ns['_ih']:
                rpt_add(line)
            rpt_add('\n*** Last line of input (may not be in above history):\n')
            rpt_add(self.app.shell._last_input_line+'\n')
        except:
            pass

        return ''.join(report)

#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------
flags = dict(base_flags)
flags.update(shell_flags)
frontend_flags = {}
addflag = lambda *args: frontend_flags.update(boolean_flag(*args))
addflag('autoedit-syntax', 'TerminalInteractiveShell.autoedit_syntax',
        'Turn on auto editing of files with syntax errors.',
        'Turn off auto editing of files with syntax errors.'
)
addflag('banner', 'TerminalIPythonApp.display_banner',
        "Display a banner upon starting IPython.",
        "Don't display a banner upon starting IPython."
)
addflag('confirm-exit', 'TerminalInteractiveShell.confirm_exit',
    """Set to confirm when you try to exit IPython with an EOF (Control-D
    in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
    you can force a direct exit without any confirmation.""",
    "Don't prompt the user when exiting."
)
addflag('term-title', 'TerminalInteractiveShell.term_title',
    "Enable auto setting the terminal title.",
    "Disable auto setting the terminal title."
)
classic_config = Config()
classic_config.InteractiveShell.cache_size = 0
classic_config.PlainTextFormatter.pprint = False
classic_config.PromptManager.in_template = '>>> '
classic_config.PromptManager.in2_template = '... '
classic_config.PromptManager.out_template = ''
classic_config.InteractiveShell.separate_in = ''
classic_config.InteractiveShell.separate_out = ''
classic_config.InteractiveShell.separate_out2 = ''
classic_config.InteractiveShell.colors = 'NoColor'
classic_config.InteractiveShell.xmode = 'Plain'

frontend_flags['classic']=(
    classic_config,
    "Gives IPython a similar feel to the classic Python prompt."
)
# # log doesn't make so much sense this way anymore
# paa('--log','-l',
#     action='store_true', dest='InteractiveShell.logstart',
#     help="Start logging to the default log file (./ipython_log.py).")
#
# # quick is harder to implement
frontend_flags['quick']=(
    {'TerminalIPythonApp' : {'quick' : True}},
    "Enable quick startup with no config files."
)

frontend_flags['i'] = (
    {'TerminalIPythonApp' : {'force_interact' : True}},
    """If running code from the command line, become interactive afterwards.
    Note: can also be given simply as '-i.'"""
)
flags.update(frontend_flags)

aliases = dict(base_aliases)
aliases.update(shell_aliases)

#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------


class LocateIPythonApp(BaseIPythonApplication):
    description = """print the path to the IPython dir"""
    subcommands = Dict(dict(
        profile=('IPython.core.profileapp.ProfileLocate',
            "print the path to an IPython profile directory",
        ),
    ))
    def start(self):
        if self.subapp is not None:
            return self.subapp.start()
        else:
            print self.ipython_dir


class TerminalIPythonApp(BaseIPythonApplication, InteractiveShellApp):
    name = u'ipython'
    description = usage.cl_usage
    default_config_file_name = default_config_file_name
    crash_handler_class = IPAppCrashHandler
    examples = _examples

    flags = Dict(flags)
    aliases = Dict(aliases)
    classes = List()
    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        return [
            InteractiveShellApp, # ShellApp comes before TerminalApp, because
            self.__class__,      # it will also affect subclasses (e.g. QtConsole)
            TerminalInteractiveShell,
            PromptManager,
            HistoryManager,
            ProfileDir,
            PlainTextFormatter,
            IPCompleter,
            ScriptMagics,
        ]

    subcommands = Dict(dict(
        qtconsole=('IPython.frontend.qt.console.qtconsoleapp.IPythonQtConsoleApp',
            """Launch the IPython Qt Console."""
        ),
        notebook=('IPython.frontend.html.notebook.notebookapp.NotebookApp',
            """Launch the IPython HTML Notebook Server."""
        ),
        profile = ("IPython.core.profileapp.ProfileApp",
            "Create and manage IPython profiles."
        ),
        kernel = ("IPython.zmq.ipkernel.IPKernelApp",
            "Start a kernel without an attached frontend."
        ),
        console=('IPython.frontend.terminal.console.app.ZMQTerminalIPythonApp',
            """Launch the IPython terminal-based Console."""
        ),
        locate=('IPython.frontend.terminal.ipapp.LocateIPythonApp',
            LocateIPythonApp.description
        ),
    ))

    # *do* autocreate requested profile, but don't create the config file.
    auto_create=Bool(True)
    # configurables
    ignore_old_config=Bool(False, config=True,
        help="Suppress warning messages about legacy config files"
    )
    quick = Bool(False, config=True,
        help="""Start IPython quickly by skipping the loading of config files."""
    )
    def _quick_changed(self, name, old, new):
        if new:
            self.load_config_file = lambda *a, **kw: None
            self.ignore_old_config=True

    display_banner = Bool(True, config=True,
        help="Whether to display a banner upon starting IPython."
    )

    # if there is code of files to run from the cmd line, don't interact
    # unless the --i flag (App.force_interact) is true.
    force_interact = Bool(False, config=True,
        help="""If a command or file is given via the command-line,
        e.g. 'ipython foo.py"""
    )
    def _force_interact_changed(self, name, old, new):
        if new:
            self.interact = True

    def _file_to_run_changed(self, name, old, new):
        if new:
            self.something_to_run = True
        if new and not self.force_interact:
                self.interact = False
    _code_to_run_changed = _file_to_run_changed
    _module_to_run_changed = _file_to_run_changed

    # internal, not-configurable
    interact=Bool(True)
    something_to_run=Bool(False)

    def parse_command_line(self, argv=None):
        """override to allow old '-pylab' flag with deprecation warning"""

        argv = sys.argv[1:] if argv is None else argv

        if '-pylab' in argv:
            # deprecated `-pylab` given,
            # warn and transform into current syntax
            argv = argv[:] # copy, don't clobber
            idx = argv.index('-pylab')
            warn.warn("`-pylab` flag has been deprecated.\n"
            "    Use `--pylab` instead, or `--pylab=foo` to specify a backend.")
            sub = '--pylab'
            if len(argv) > idx+1:
                # check for gui arg, as in '-pylab qt'
                gui = argv[idx+1]
                if gui in ('wx', 'qt', 'qt4', 'gtk', 'auto'):
                    sub = '--pylab='+gui
                    argv.pop(idx+1)
            argv[idx] = sub

        return super(TerminalIPythonApp, self).parse_command_line(argv)
    
    @catch_config_error
    def initialize(self, argv=None):
        """Do actions after construct, but before starting the app."""
        super(TerminalIPythonApp, self).initialize(argv)
        if self.subapp is not None:
            # don't bother initializing further, starting subapp
            return
        if not self.ignore_old_config:
            check_for_old_config(self.ipython_dir)
        # print self.extra_args
        if self.extra_args and not self.something_to_run:
            self.file_to_run = self.extra_args[0]
        self.init_path()
        # create the shell
        self.init_shell()
        # and draw the banner
        self.init_banner()
        # Now a variety of things that happen after the banner is printed.
        self.init_gui_pylab()
        self.init_extensions()
        self.init_code()

    def init_shell(self):
        """initialize the InteractiveShell instance"""
        # Create an InteractiveShell instance.
        # shell.display_banner should always be False for the terminal
        # based app, because we call shell.show_banner() by hand below
        # so the banner shows *before* all extension loading stuff.
        self.shell = TerminalInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir)
        self.shell.configurables.append(self)

    def init_banner(self):
        """optionally display the banner"""
        if self.display_banner and self.interact:
            self.shell.show_banner()
        # Make sure there is a space below the banner.
        if self.log_level <= logging.INFO: print

    def _pylab_changed(self, name, old, new):
        """Replace --pylab='inline' with --pylab='auto'"""
        if new == 'inline':
            warn.warn("'inline' not available as pylab backend, "
                      "using 'auto' instead.")
            self.pylab = 'auto'

    def start(self):
        if self.subapp is not None:
            return self.subapp.start()
        # perform any prexec steps:
        if self.interact:
            self.log.debug("Starting IPython's mainloop...")
            self.shell.mainloop()
        else:
            self.log.debug("IPython not interactive...")


def load_default_config(ipython_dir=None):
    """Load the default config file from the default ipython_dir.

    This is useful for embedded shells.
    """
    if ipython_dir is None:
        ipython_dir = get_ipython_dir()
    profile_dir = os.path.join(ipython_dir, 'profile_default')
    cl = PyFileConfigLoader(default_config_file_name, profile_dir)
    try:
        config = cl.load_config()
    except ConfigFileNotFound:
        # no config found
        config = Config()
    return config


def launch_new_instance():
    """Create and run a full blown IPython instance"""
    app = TerminalIPythonApp.instance()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()
