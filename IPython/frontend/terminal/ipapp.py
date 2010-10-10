#!/usr/bin/env python
# encoding: utf-8
"""
The :class:`~IPython.core.application.Application` object for the command
line :command:`ipython` program.

Authors
-------

* Brian Granger
* Fernando Perez
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

from IPython.core import release
from IPython.core.crashhandler import CrashHandler
from IPython.core.application import Application, BaseAppConfigLoader
from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
from IPython.config.loader import (
    Config,
    PyFileConfigLoader
)
from IPython.lib import inputhook
from IPython.utils.path import filefind, get_ipython_dir
from IPython.core import usage

#-----------------------------------------------------------------------------
# Globals, utilities and helpers
#-----------------------------------------------------------------------------

#: The default config file name for this application.
default_config_file_name = u'ipython_config.py'


class IPAppConfigLoader(BaseAppConfigLoader):

    def _add_arguments(self):
        super(IPAppConfigLoader, self)._add_arguments()
        paa = self.parser.add_argument
        paa('-p', 
            '--profile', dest='Global.profile', type=unicode,
            help=
            """The string name of the ipython profile to be used.  Assume that your
            config file is ipython_config-<name>.py (looks in current dir first,
            then in IPYTHON_DIR). This is a quick way to keep and load multiple
            config files for different tasks, especially if include your basic one
            in your more specialized ones.  You can keep a basic
            IPYTHON_DIR/ipython_config.py file and then have other 'profiles' which
            include this one and load extra things for particular tasks.""",
            metavar='Global.profile')
        paa('--config-file', 
            dest='Global.config_file', type=unicode,
            help=
            """Set the config file name to override default.  Normally IPython
            loads ipython_config.py (from current directory) or
            IPYTHON_DIR/ipython_config.py.  If the loading of your config file
            fails, IPython starts with a bare bones configuration (no modules
            loaded at all).""",
            metavar='Global.config_file')
        paa('--autocall', 
            dest='InteractiveShell.autocall', type=int, 
            help=
            """Make IPython automatically call any callable object even if you
            didn't type explicit parentheses. For example, 'str 43' becomes
            'str(43)' automatically.  The value can be '0' to disable the feature,
            '1' for 'smart' autocall, where it is not applied if there are no more
            arguments on the line, and '2' for 'full' autocall, where all callable
            objects are automatically called (even if no arguments are present).
            The default is '1'.""",
            metavar='InteractiveShell.autocall')
        paa('--autoindent',
            action='store_true', dest='InteractiveShell.autoindent',
            help='Turn on autoindenting.')
        paa('--no-autoindent',
            action='store_false', dest='InteractiveShell.autoindent',
            help='Turn off autoindenting.')
        paa('--automagic',
            action='store_true', dest='InteractiveShell.automagic',
            help=
            """Turn on the auto calling of magic commands. Type %%magic at the
            IPython  prompt  for  more information.""")
        paa('--no-automagic',
            action='store_false', dest='InteractiveShell.automagic',
            help='Turn off the auto calling of magic commands.')
        paa('--autoedit-syntax',
            action='store_true', dest='TerminalInteractiveShell.autoedit_syntax',
            help='Turn on auto editing of files with syntax errors.')
        paa('--no-autoedit-syntax',
            action='store_false', dest='TerminalInteractiveShell.autoedit_syntax',
            help='Turn off auto editing of files with syntax errors.')
        paa('--banner',
            action='store_true', dest='Global.display_banner',
            help='Display a banner upon starting IPython.')
        paa('--no-banner',
            action='store_false', dest='Global.display_banner',
            help="Don't display a banner upon starting IPython.")
        paa('--cache-size',
            type=int, dest='InteractiveShell.cache_size',
            help=
            """Set the size of the output cache.  The default is 1000, you can
            change it permanently in your config file.  Setting it to 0 completely
            disables the caching system, and the minimum value accepted is 20 (if
            you provide a value less than 20, it is reset to 0 and a warning is
            issued).  This limit is defined because otherwise you'll spend more
            time re-flushing a too small cache than working""",
            metavar='InteractiveShell.cache_size')
        paa('--classic',
            action='store_true', dest='Global.classic',
            help="Gives IPython a similar feel to the classic Python prompt.")
        paa('--colors',
            type=str, dest='InteractiveShell.colors',
            help="Set the color scheme (NoColor, Linux, and LightBG).",
            metavar='InteractiveShell.colors')
        paa('--color-info',
            action='store_true', dest='InteractiveShell.color_info',
            help=
            """IPython can display information about objects via a set of func-
            tions, and optionally can use colors for this, syntax highlighting
            source code and various other elements.  However, because this
            information is passed through a pager (like 'less') and many pagers get
            confused with color codes, this option is off by default.  You can test
            it and turn it on permanently in your ipython_config.py file if it
            works for you.  Test it and turn it on permanently if it works with
            your system.  The magic function %%color_info allows you to toggle this
            inter- actively for testing.""")
        paa('--no-color-info',
            action='store_false', dest='InteractiveShell.color_info',
            help="Disable using colors for info related things.")
        paa('--confirm-exit',
            action='store_true', dest='TerminalInteractiveShell.confirm_exit',
            help=
            """Set to confirm when you try to exit IPython with an EOF (Control-D
            in Unix, Control-Z/Enter in Windows). By typing 'exit', 'quit' or
            '%%Exit', you can force a direct exit without any confirmation.""")
        paa('--no-confirm-exit',
            action='store_false', dest='TerminalInteractiveShell.confirm_exit',
            help="Don't prompt the user when exiting.")
        paa('--deep-reload',
            action='store_true', dest='InteractiveShell.deep_reload',
            help=
            """Enable deep (recursive) reloading by default. IPython can use the
            deep_reload module which reloads changes in modules recursively (it
            replaces the reload() function, so you don't need to change anything to
            use it). deep_reload() forces a full reload of modules whose code may
            have changed, which the default reload() function does not.  When
            deep_reload is off, IPython will use the normal reload(), but
            deep_reload will still be available as dreload(). This fea- ture is off
            by default [which means that you have both normal reload() and
            dreload()].""")
        paa('--no-deep-reload',
            action='store_false', dest='InteractiveShell.deep_reload',
            help="Disable deep (recursive) reloading by default.")
        paa('--editor',
            type=str, dest='TerminalInteractiveShell.editor',
            help="Set the editor used by IPython (default to $EDITOR/vi/notepad).",
            metavar='TerminalInteractiveShell.editor')
        paa('--log','-l', 
            action='store_true', dest='InteractiveShell.logstart',
            help="Start logging to the default log file (./ipython_log.py).")
        paa('--logfile','-lf',
            type=unicode, dest='InteractiveShell.logfile',
            help="Start logging to logfile with this name.",
            metavar='InteractiveShell.logfile')
        paa('--log-append','-la',
            type=unicode, dest='InteractiveShell.logappend',
            help="Start logging to the given file in append mode.",
            metavar='InteractiveShell.logfile')
        paa('--pdb',
            action='store_true', dest='InteractiveShell.pdb',
            help="Enable auto calling the pdb debugger after every exception.")
        paa('--no-pdb',
            action='store_false', dest='InteractiveShell.pdb',
            help="Disable auto calling the pdb debugger after every exception.")
        paa('--pprint',
            action='store_true', dest='InteractiveShell.pprint',
            help="Enable auto pretty printing of results.")
        paa('--no-pprint',
            action='store_false', dest='InteractiveShell.pprint',
            help="Disable auto auto pretty printing of results.")
        paa('--prompt-in1','-pi1',
            type=str, dest='InteractiveShell.prompt_in1',
            help=
            """Set the main input prompt ('In [\#]: ').  Note that if you are using
            numbered prompts, the number is represented with a '\#' in the string.
            Don't forget to quote strings with spaces embedded in them. Most
            bash-like escapes can be used to customize IPython's prompts, as well
            as a few additional ones which are IPython-spe- cific.  All valid
            prompt escapes are described in detail in the Customization section of
            the IPython manual.""",
            metavar='InteractiveShell.prompt_in1')
        paa('--prompt-in2','-pi2',
            type=str, dest='InteractiveShell.prompt_in2',
            help=
            """Set the secondary input prompt (' .\D.: ').  Similar to the previous
            option, but used for the continuation prompts. The special sequence
            '\D' is similar to '\#', but with all digits replaced by dots (so you
            can have your continuation prompt aligned with your input prompt).
            Default: ' .\D.: ' (note three spaces at the start for alignment with
            'In [\#]')""",
            metavar='InteractiveShell.prompt_in2')
        paa('--prompt-out','-po',
            type=str, dest='InteractiveShell.prompt_out',
            help="Set the output prompt ('Out[\#]:')",
            metavar='InteractiveShell.prompt_out')
        paa('--quick',
            action='store_true', dest='Global.quick',
            help="Enable quick startup with no config files.")
        paa('--readline',
            action='store_true', dest='InteractiveShell.readline_use',
            help="Enable readline for command line usage.")
        paa('--no-readline',
            action='store_false', dest='InteractiveShell.readline_use',
            help="Disable readline for command line usage.")
        paa('--screen-length','-sl',
            type=int, dest='TerminalInteractiveShell.screen_length',
            help=
            """Number of lines of your screen, used to control printing of very
            long strings.  Strings longer than this number of lines will be sent
            through a pager instead of directly printed.  The default value for
            this is 0, which means IPython will auto-detect your screen size every
            time it needs to print certain potentially long strings (this doesn't
            change the behavior of the 'print' keyword, it's only triggered
            internally). If for some reason this isn't working well (it needs
            curses support), specify it yourself. Otherwise don't change the
            default.""",
            metavar='TerminalInteractiveShell.screen_length')
        paa('--separate-in','-si',
            type=str, dest='InteractiveShell.separate_in',
            help="Separator before input prompts.  Default '\\n'.",
            metavar='InteractiveShell.separate_in')
        paa('--separate-out','-so',
            type=str, dest='InteractiveShell.separate_out',
            help="Separator before output prompts.  Default 0 (nothing).",
            metavar='InteractiveShell.separate_out')
        paa('--separate-out2','-so2', 
            type=str, dest='InteractiveShell.separate_out2',
            help="Separator after output prompts.  Default 0 (nonight).",
            metavar='InteractiveShell.separate_out2')
        paa('--no-sep',
            action='store_true', dest='Global.nosep',
            help="Eliminate all spacing between prompts.")
        paa('--term-title',
            action='store_true', dest='TerminalInteractiveShell.term_title',
            help="Enable auto setting the terminal title.")
        paa('--no-term-title',
            action='store_false', dest='TerminalInteractiveShell.term_title',
            help="Disable auto setting the terminal title.")
        paa('--xmode',
            type=str, dest='InteractiveShell.xmode',
            help=
            """Exception reporting mode ('Plain','Context','Verbose').  Plain:
            similar to python's normal traceback printing.  Context: prints 5 lines
            of context source code around each line in the traceback.  Verbose:
            similar to Context, but additionally prints the variables currently
            visible where the exception happened (shortening their strings if too
            long).  This can potentially be very slow, if you happen to have a huge
            data structure whose string representation is complex to compute.
            Your computer may appear to freeze for a while with cpu usage at 100%%.
            If this occurs, you can cancel the traceback with Ctrl-C (maybe hitting
            it more than once).
            """,
            metavar='InteractiveShell.xmode')
        paa('--ext',
            type=str, dest='Global.extra_extension',
            help="The dotted module name of an IPython extension to load.",
            metavar='Global.extra_extension')
        paa('-c',
            type=str, dest='Global.code_to_run',
            help="Execute the given command string.",
            metavar='Global.code_to_run')
        paa('-i',
            action='store_true', dest='Global.force_interact',
            help=
            "If running code from the command line, become interactive afterwards.")

        # Options to start with GUI control enabled from the beginning
        paa('--gui',
            type=str, dest='Global.gui',
            help="Enable GUI event loop integration ('qt', 'wx', 'gtk').",
            metavar='gui-mode')
        paa('--pylab','-pylab',
            type=str, dest='Global.pylab',
            nargs='?', const='auto', metavar='gui-mode',
            help="Pre-load matplotlib and numpy for interactive use. "+
            "If no value is given, the gui backend is matplotlib's, else use "+
            "one of:  ['tk', 'qt', 'wx', 'gtk'].")

        # Legacy GUI options.  Leave them in for backwards compatibility, but the
        # 'thread' names are really a misnomer now.
        paa('--wthread', '-wthread',
            action='store_true', dest='Global.wthread',
            help=
            """Enable wxPython event loop integration. (DEPRECATED, use --gui wx)""")
        paa('--q4thread', '--qthread', '-q4thread', '-qthread',
            action='store_true', dest='Global.q4thread',
            help=
            """Enable Qt4 event loop integration. Qt3 is no longer supported.
            (DEPRECATED, use --gui qt)""")
        paa('--gthread', '-gthread',
            action='store_true', dest='Global.gthread',
            help=
            """Enable GTK event loop integration. (DEPRECATED, use --gui gtk)""")


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
        bug_tracker = 'https://bugs.launchpad.net/ipython/+filebug'
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
# Main classes and functions
#-----------------------------------------------------------------------------

class IPythonApp(Application):
    name = u'ipython'
    #: argparse formats better the 'usage' than the 'description' field
    description = None
    usage = usage.cl_usage
    command_line_loader = IPAppConfigLoader
    default_config_file_name = default_config_file_name
    crash_handler_class = IPAppCrashHandler

    def create_default_config(self):
        super(IPythonApp, self).create_default_config()
        # Eliminate multiple lookups
        Global = self.default_config.Global

        # Set all default values
        Global.display_banner = True
        
        # If the -c flag is given or a file is given to run at the cmd line
        # like "ipython foo.py", normally we exit without starting the main
        # loop.  The force_interact config variable allows a user to override
        # this and interact.  It is also set by the -i cmd line flag, just
        # like Python.
        Global.force_interact = False

        # By default always interact by starting the IPython mainloop.
        Global.interact = True

        # No GUI integration by default
        Global.gui = False
        # Pylab off by default
        Global.pylab = False

        # Deprecated versions of gui support that used threading, we support
        # them just for bacwards compatibility as an alternate spelling for
        # '--gui X'
        Global.qthread = False
        Global.q4thread = False
        Global.wthread = False
        Global.gthread = False

    def load_file_config(self):
        if hasattr(self.command_line_config.Global, 'quick'):
            if self.command_line_config.Global.quick:
                self.file_config = Config()
                return
        super(IPythonApp, self).load_file_config()

    def post_load_file_config(self):
        if hasattr(self.command_line_config.Global, 'extra_extension'):
            if not hasattr(self.file_config.Global, 'extensions'):
                self.file_config.Global.extensions = []
            self.file_config.Global.extensions.append(
                self.command_line_config.Global.extra_extension)
            del self.command_line_config.Global.extra_extension

    def pre_construct(self):
        config = self.master_config

        if hasattr(config.Global, 'classic'):
            if config.Global.classic:
                config.InteractiveShell.cache_size = 0
                config.InteractiveShell.pprint = 0
                config.InteractiveShell.prompt_in1 = '>>> '
                config.InteractiveShell.prompt_in2 = '... '
                config.InteractiveShell.prompt_out = ''
                config.InteractiveShell.separate_in = \
                    config.InteractiveShell.separate_out = \
                    config.InteractiveShell.separate_out2 = ''
                config.InteractiveShell.colors = 'NoColor'
                config.InteractiveShell.xmode = 'Plain'

        if hasattr(config.Global, 'nosep'):
            if config.Global.nosep:
                config.InteractiveShell.separate_in = \
                config.InteractiveShell.separate_out = \
                config.InteractiveShell.separate_out2 = ''

        # if there is code of files to run from the cmd line, don't interact
        # unless the -i flag (Global.force_interact) is true.
        code_to_run = config.Global.get('code_to_run','')
        file_to_run = False
        if self.extra_args and self.extra_args[0]:
                file_to_run = True
        if file_to_run or code_to_run:
            if not config.Global.force_interact:
                config.Global.interact = False

    def construct(self):
        # I am a little hesitant to put these into InteractiveShell itself.
        # But that might be the place for them
        sys.path.insert(0, '')

        # Create an InteractiveShell instance.
        self.shell = TerminalInteractiveShell.instance(config=self.master_config)

    def post_construct(self):
        """Do actions after construct, but before starting the app."""
        config = self.master_config
        
        # shell.display_banner should always be False for the terminal 
        # based app, because we call shell.show_banner() by hand below
        # so the banner shows *before* all extension loading stuff.
        self.shell.display_banner = False
        if config.Global.display_banner and \
            config.Global.interact:
            self.shell.show_banner()

        # Make sure there is a space below the banner.
        if self.log_level <= logging.INFO: print

        # Now a variety of things that happen after the banner is printed.
        self._enable_gui_pylab()
        self._load_extensions()
        self._run_exec_lines()
        self._run_exec_files()
        self._run_cmd_line_code()

    def _enable_gui_pylab(self):
        """Enable GUI event loop integration, taking pylab into account."""
        Global = self.master_config.Global

        # Select which gui to use
        if Global.gui:
            gui = Global.gui
        # The following are deprecated, but there's likely to be a lot of use
        # of this form out there, so we might as well support it for now.  But
        # the --gui option above takes precedence.
        elif Global.wthread:
            gui = inputhook.GUI_WX
        elif Global.qthread:
            gui = inputhook.GUI_QT
        elif Global.gthread:
            gui = inputhook.GUI_GTK
        else:
            gui = None

        # Using --pylab will also require gui activation, though which toolkit
        # to use may be chosen automatically based on mpl configuration.
        if Global.pylab:
            activate = self.shell.enable_pylab
            if Global.pylab == 'auto':
                gui = None
            else:
                gui = Global.pylab
        else:
            # Enable only GUI integration, no pylab
            activate = inputhook.enable_gui

        if gui or Global.pylab:
            try:
                self.log.info("Enabling GUI event loop integration, "
                              "toolkit=%s, pylab=%s" % (gui, Global.pylab) )
                activate(gui)
            except:
                self.log.warn("Error in enabling GUI event loop integration:")
                self.shell.showtraceback()

    def _load_extensions(self):
        """Load all IPython extensions in Global.extensions.

        This uses the :meth:`ExtensionManager.load_extensions` to load all
        the extensions listed in ``self.master_config.Global.extensions``.
        """
        try:
            if hasattr(self.master_config.Global, 'extensions'):
                self.log.debug("Loading IPython extensions...")
                extensions = self.master_config.Global.extensions
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

    def _run_exec_lines(self):
        """Run lines of code in Global.exec_lines in the user's namespace."""
        try:
            if hasattr(self.master_config.Global, 'exec_lines'):
                self.log.debug("Running code from Global.exec_lines...")
                exec_lines = self.master_config.Global.exec_lines
                for line in exec_lines:
                    try:
                        self.log.info("Running code in user namespace: %s" %
                                      line)
                        self.shell.run_cell(line)
                    except:
                        self.log.warn("Error in executing line in user "
                                      "namespace: %s" % line)
                        self.shell.showtraceback()
        except:
            self.log.warn("Unknown error in handling Global.exec_lines:")
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
        try:
            if hasattr(self.master_config.Global, 'exec_files'):
                self.log.debug("Running files in Global.exec_files...")
                exec_files = self.master_config.Global.exec_files
                for fname in exec_files:
                    self._exec_file(fname)
        except:
            self.log.warn("Unknown error in handling Global.exec_files:")
            self.shell.showtraceback()

    def _run_cmd_line_code(self):
        if hasattr(self.master_config.Global, 'code_to_run'):
            line = self.master_config.Global.code_to_run
            try:
                self.log.info("Running code given at command line (-c): %s" %
                              line)
                self.shell.run_cell(line)
            except:
                self.log.warn("Error in executing line in user namespace: %s" %
                              line)
                self.shell.showtraceback()
            return
        # Like Python itself, ignore the second if the first of these is present
        try:
            fname = self.extra_args[0]
        except:
            pass
        else:
            try:
                self._exec_file(fname)
            except:
                self.log.warn("Error in executing file in user namespace: %s" %
                              fname)
                self.shell.showtraceback()

    def start_app(self):
        if self.master_config.Global.interact:
            self.log.debug("Starting IPython's mainloop...")
            self.shell.mainloop()
        else:
            self.log.debug("IPython not interactive, start_app is no-op...")


def load_default_config(ipython_dir=None):
    """Load the default config file from the default ipython_dir.

    This is useful for embedded shells.
    """
    if ipython_dir is None:
        ipython_dir = get_ipython_dir()
    cl = PyFileConfigLoader(default_config_file_name, ipython_dir)
    config = cl.load_config()
    return config


def launch_new_instance():
    """Create and run a full blown IPython instance"""
    app = IPythonApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()
