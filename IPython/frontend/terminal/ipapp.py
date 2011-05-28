#!/usr/bin/env python
# encoding: utf-8
"""
The :class:`~IPython.core.newapplication.Application` object for the command
line :command:`ipython` program.

Authors
-------

* Brian Granger
* Fernando Perez
* Min Ragan-Kelley
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2010  The IPython Development Team
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
    Config, PyFileConfigLoader
)
from IPython.config.application import boolean_flag
from IPython.core import release
from IPython.core import usage
from IPython.core.crashhandler import CrashHandler
from IPython.core.formatters import PlainTextFormatter
from IPython.core.newapplication import (
    ProfileDir, BaseIPythonApplication, base_flags, base_aliases
)
from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
from IPython.lib import inputhook
from IPython.utils.path import filefind, get_ipython_dir, check_for_old_config
from IPython.utils.traitlets import (
    Bool, Unicode, Dict, Instance, List,CaselessStrEnum
)

#-----------------------------------------------------------------------------
# Globals, utilities and helpers
#-----------------------------------------------------------------------------

#: The default config file name for this application.
default_config_file_name = u'ipython_config.py'



#-----------------------------------------------------------------------------
# Crash handler for this application
#-----------------------------------------------------------------------------

_message_template = """\
Oops, $self.app_name crashed. We do our best to make it stable, but...

A crash report was automatically generated with the following information:
  - A verbatim copy of the crash traceback.
  - A copy of your input history during this session.
  - Data on your current $self.app_name configuration.

It was left in the file named:
\t'$self.crash_report_fname'
If you can email this file to the developers, the information in it will help
them in understanding and correcting the problem.

You can mail it to: $self.contact_name at $self.contact_email
with the subject '$self.app_name Crash Report'.

If you want to do it now, the following command will work (under Unix):
mail -s '$self.app_name Crash Report' $self.contact_email < $self.crash_report_fname

To ensure accurate tracking of this issue, please file a report about it at:
$self.bug_tracker
"""

class IPAppCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    message_template = _message_template

    def __init__(self, app):
        contact_name = release.authors['Fernando'][0]
        contact_email = release.authors['Fernando'][1]
        bug_tracker = 'http://github.com/ipython/ipython/issues'
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
flags.update({


})
addflag = lambda *args: flags.update(boolean_flag(*args))
addflag('autoindent', 'InteractiveShell.autoindent',
        'Turn on autoindenting.', 'Turn off autoindenting.'
)
addflag('automagic', 'InteractiveShell.automagic',
        """Turn on the auto calling of magic commands. Type %%magic at the
        IPython  prompt  for  more information.""",
        'Turn off the auto calling of magic commands.'
)
addflag('autoedit-syntax', 'TerminalInteractiveShell.autoedit_syntax',
        'Turn on auto editing of files with syntax errors.',
        'Turn off auto editing of files with syntax errors.'
)
addflag('banner', 'IPythonApp.display_banner',
        "Display a banner upon starting IPython.",
        "Don't display a banner upon starting IPython."
)
addflag('pdb', 'InteractiveShell.pdb',
    "Enable auto calling the pdb debugger after every exception.",
    "Disable auto calling the pdb debugger after every exception."
)
addflag('pprint', 'PlainTextFormatter.pprint',
    "Enable auto pretty printing of results.",
    "Disable auto auto pretty printing of results."
)
addflag('color-info', 'InteractiveShell.color_info',
    """IPython can display information about objects via a set of func-
    tions, and optionally can use colors for this, syntax highlighting
    source code and various other elements.  However, because this
    information is passed through a pager (like 'less') and many pagers get
    confused with color codes, this option is off by default.  You can test
    it and turn it on permanently in your ipython_config.py file if it
    works for you.  Test it and turn it on permanently if it works with
    your system.  The magic function %%color_info allows you to toggle this
    inter- actively for testing.""",
    "Disable using colors for info related things."
)
addflag('confirm-exit', 'TerminalInteractiveShell.confirm_exit',
    """Set to confirm when you try to exit IPython with an EOF (Control-D
    in Unix, Control-Z/Enter in Windows). By typing 'exit', 'quit' or
    '%%Exit', you can force a direct exit without any confirmation.""",
    "Don't prompt the user when exiting."
)
addflag('deep-reload', 'InteractiveShell.deep_reload',
    """Enable deep (recursive) reloading by default. IPython can use the
    deep_reload module which reloads changes in modules recursively (it
    replaces the reload() function, so you don't need to change anything to
    use it). deep_reload() forces a full reload of modules whose code may
    have changed, which the default reload() function does not.  When
    deep_reload is off, IPython will use the normal reload(), but
    deep_reload will still be available as dreload(). This fea- ture is off
    by default [which means that you have both normal reload() and
    dreload()].""",
    "Disable deep (recursive) reloading by default."
)
addflag('readline', 'InteractiveShell.readline_use',
    "Enable readline for command line usage.",
    "Disable readline for command line usage."
)
addflag('term-title', 'TerminalInteractiveShell.term_title',
    "Enable auto setting the terminal title.",
    "Disable auto setting the terminal title."
)
classic_config = Config()
classic_config.InteractiveShell.cache_size = 0
classic_config.PlainTextFormatter.pprint = False
classic_config.InteractiveShell.prompt_in1 = '>>> '
classic_config.InteractiveShell.prompt_in2 = '... '
classic_config.InteractiveShell.prompt_out = ''
classic_config.InteractiveShell.separate_in = ''
classic_config.InteractiveShell.separate_out = ''
classic_config.InteractiveShell.separate_out2 = ''
classic_config.InteractiveShell.colors = 'NoColor'
classic_config.InteractiveShell.xmode = 'Plain'

flags['classic']=(
    classic_config,
    "Gives IPython a similar feel to the classic Python prompt."
)
# # log doesn't make so much sense this way anymore
# paa('--log','-l',
#     action='store_true', dest='InteractiveShell.logstart',
#     help="Start logging to the default log file (./ipython_log.py).")
#
# # quick is harder to implement
flags['quick']=(
    {'IPythonApp' : {'quick' : True}},
    "Enable quick startup with no config files."
)

nosep_config = Config()
nosep_config.InteractiveShell.separate_in = ''
nosep_config.InteractiveShell.separate_out = ''
nosep_config.InteractiveShell.separate_out2 = ''

flags['nosep']=(nosep_config, "Eliminate all spacing between prompts.")

flags['i'] = (
    {'IPythonApp' : {'force_interact' : True}},
    "If running code from the command line, become interactive afterwards."
)
flags['pylab'] = (
    {'IPythonApp' : {'pylab' : 'auto'}},
    """Pre-load matplotlib and numpy for interactive use with
    the default matplotlib backend."""
)

aliases = dict(base_aliases)

# it's possible we don't want short aliases for *all* of these:
aliases.update(dict(
    autocall='InteractiveShell.autocall',
    cache_size='InteractiveShell.cache_size',
    colors='InteractiveShell.colors',
    editor='TerminalInteractiveShell.editor',
    logfile='InteractiveShell.logfile',
    log_append='InteractiveShell.logappend',
    pi1='InteractiveShell.prompt_in1',
    pi2='InteractiveShell.prompt_in1',
    po='InteractiveShell.prompt_out',
    sl='TerminalInteractiveShell.screen_length',
    si='InteractiveShell.separate_in',
    so='InteractiveShell.separate_out',
    so2='InteractiveShell.separate_out2',
    xmode='InteractiveShell.xmode',
    c='IPythonApp.code_to_run',
    ext='IPythonApp.extra_extension',
    gui='IPythonApp.gui',
    pylab='IPythonApp.pylab',
))

#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------

class IPythonApp(BaseIPythonApplication):
    name = u'ipython'
    description = usage.cl_usage
    # command_line_loader = IPAppConfigLoader
    default_config_file_name = default_config_file_name
    crash_handler_class = IPAppCrashHandler
    flags = Dict(flags)
    aliases = Dict(aliases)
    classes = [TerminalInteractiveShell, ProfileDir, PlainTextFormatter]
    # *do* autocreate requested profile
    auto_create=Bool(True)
    copy_config_files=Bool(True)
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

    gui = CaselessStrEnum(('qt','wx','gtk'), config=True,
        help="Enable GUI event loop integration ('qt', 'wx', 'gtk')."
    )
    pylab = CaselessStrEnum(['tk', 'qt', 'wx', 'gtk', 'osx', 'auto'],
        config=True,
        help="""Pre-load matplotlib and numpy for interactive use,
        selecting a particular matplotlib backend and loop integration.
        """
    )
    display_banner = Bool(True, config=True,
        help="Whether to display a banner upon starting IPython."
    )
    extensions = List(Unicode, config=True,
        help="A list of dotted module names of IPython extensions to load."
    )
    extra_extension = Unicode('', config=True,
        help="dotted module name of an IPython extension to load."
    )
    def _extra_extension_changed(self, name, old, new):
        if new:
            # add to self.extensions
            self.extensions.append(new)

    # if there is code of files to run from the cmd line, don't interact
    # unless the --i flag (App.force_interact) is true.
    force_interact = Bool(False, config=True,
        help="""If a command or file is given via the command-line,
        e.g. 'ipython foo.py"""
    )
    def _force_interact_changed(self, name, old, new):
        if new:
            self.interact = True

    exec_files = List(Unicode, config=True,
        help="""List of files to run at IPython startup."""
    )
    file_to_run = Unicode('', config=True,
        help="""A file to be run""")
    def _file_to_run_changed(self, name, old, new):
        if new and not self.force_interact:
                self.interact = False

    exec_lines = List(Unicode, config=True,
        help="""lines of code to run at IPython startup."""
    )
    code_to_run = Unicode('', config=True,
        help="Execute the given command string."
    )
    _code_to_run_changed = _file_to_run_changed

    # internal, not-configurable
    interact=Bool(True)


    def initialize(self, argv=None):
        """Do actions after construct, but before starting the app."""
        super(IPythonApp, self).initialize(argv)
        if not self.ignore_old_config:
            check_for_old_config(self.ipython_dir)
        
        # print self.extra_args
        if self.extra_args:
            self.file_to_run = self.extra_args[0]
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
        # I am a little hesitant to put these into InteractiveShell itself.
        # But that might be the place for them
        sys.path.insert(0, '')

        # Create an InteractiveShell instance.
        # shell.display_banner should always be False for the terminal 
        # based app, because we call shell.show_banner() by hand below
        # so the banner shows *before* all extension loading stuff.
        self.shell = TerminalInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir)

    def init_banner(self):
        """optionally display the banner"""
        if self.display_banner and self.interact:
            self.shell.show_banner()
        # Make sure there is a space below the banner.
        if self.log_level <= logging.INFO: print


    def init_gui_pylab(self):
        """Enable GUI event loop integration, taking pylab into account."""
        gui = self.gui

        # Using `pylab` will also require gui activation, though which toolkit
        # to use may be chosen automatically based on mpl configuration.
        if self.pylab:
            activate = self.shell.enable_pylab
            if self.pylab == 'auto':
                gui = None
            else:
                gui = self.pylab
        else:
            # Enable only GUI integration, no pylab
            activate = inputhook.enable_gui

        if gui or self.pylab:
            try:
                self.log.info("Enabling GUI event loop integration, "
                              "toolkit=%s, pylab=%s" % (gui, self.pylab) )
                activate(gui)
            except:
                self.log.warn("Error in enabling GUI event loop integration:")
                self.shell.showtraceback()

    def init_extensions(self):
        """Load all IPython extensions in IPythonApp.extensions.

        This uses the :meth:`ExtensionManager.load_extensions` to load all
        the extensions listed in ``self.extensions``.
        """
        if not self.extensions:
            return
        try:
            self.log.debug("Loading IPython extensions...")
            extensions = self.extensions
            for ext in extensions:
                try:
                    self.log.info("Loading IPython extension: %s" % ext)
                    self.shell.extension_manager.load_extension(ext)
                except:
                    self.log.warn("Error in loading extension: %s" % ext)
                    self.shell.showtraceback()
        except:
            self.log.warn("Unknown error in loading extensions:")
            self.shell.showtraceback()

    def init_code(self):
        """run the pre-flight code, specified via exec_lines"""
        self._run_exec_lines()
        self._run_exec_files()
        self._run_cmd_line_code()

    def _run_exec_lines(self):
        """Run lines of code in IPythonApp.exec_lines in the user's namespace."""
        if not self.exec_lines:
            return
        try:
            self.log.debug("Running code from IPythonApp.exec_lines...")
            for line in self.exec_lines:
                try:
                    self.log.info("Running code in user namespace: %s" %
                                  line)
                    self.shell.run_cell(line, store_history=False)
                except:
                    self.log.warn("Error in executing line in user "
                                  "namespace: %s" % line)
                    self.shell.showtraceback()
        except:
            self.log.warn("Unknown error in handling IPythonApp.exec_lines:")
            self.shell.showtraceback()

    def _exec_file(self, fname):
        full_filename = filefind(fname, [u'.', self.ipython_dir])
        if os.path.isfile(full_filename):
            if full_filename.endswith(u'.py'):
                self.log.info("Running file in user namespace: %s" %
                              full_filename)
                # Ensure that __file__ is always defined to match Python behavior
                self.shell.user_ns['__file__'] = fname
                try:
                    self.shell.safe_execfile(full_filename, self.shell.user_ns)
                finally:
                    del self.shell.user_ns['__file__']
            elif full_filename.endswith('.ipy'):
                self.log.info("Running file in user namespace: %s" %
                              full_filename)
                self.shell.safe_execfile_ipy(full_filename)
            else:
                self.log.warn("File does not have a .py or .ipy extension: <%s>"
                               % full_filename)

    def _run_exec_files(self):
        """Run files from IPythonApp.exec_files"""
        if not self.exec_files:
            return

        self.log.debug("Running files in IPythonApp.exec_files...")
        try:
            for fname in self.exec_files:
                self._exec_file(fname)
        except:
            self.log.warn("Unknown error in handling IPythonApp.exec_files:")
            self.shell.showtraceback()

    def _run_cmd_line_code(self):
        """Run code or file specified at the command-line"""
        if self.code_to_run:
            line = self.code_to_run
            try:
                self.log.info("Running code given at command line (c=): %s" %
                              line)
                self.shell.run_cell(line, store_history=False)
            except:
                self.log.warn("Error in executing line in user namespace: %s" %
                              line)
                self.shell.showtraceback()

        # Like Python itself, ignore the second if the first of these is present
        elif self.file_to_run:
            fname = self.file_to_run
            try:
                self._exec_file(fname)
            except:
                self.log.warn("Error in executing file in user namespace: %s" %
                              fname)
                self.shell.showtraceback()


    def start(self):
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
    config = cl.load_config()
    return config


def launch_new_instance():
    """Create and run a full blown IPython instance"""
    app = IPythonApp()
    app.initialize()
    # print app.config
    # print app.profile_dir.location
    app.start()


if __name__ == '__main__':
    launch_new_instance()
