#!/usr/bin/env python
# encoding: utf-8
"""
The main IPython application object

Authors:

* Brian Granger
* Fernando Perez

Notes
-----
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
import warnings

from IPython.core.application import Application
from IPython.core import release
from IPython.core.iplib import InteractiveShell
from IPython.config.loader import IPythonArgParseConfigLoader, NoDefault

from IPython.utils.ipstruct import Struct


#-----------------------------------------------------------------------------
# Utilities and helpers
#-----------------------------------------------------------------------------


ipython_desc = """
A Python shell with automatic history (input and output), dynamic object
introspection, easier configuration, command completion, access to the system
shell and more.
"""

def threaded_shell_warning():
    msg = """

The IPython threaded shells and their associated command line
arguments (pylab/wthread/gthread/qthread/q4thread) have been 
deprecated.  See the %gui magic for information on the new interface.
"""
    warnings.warn(msg, category=DeprecationWarning, stacklevel=1)


#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------

cl_args = (
    (('-autocall',), dict(
        type=int, dest='AUTOCALL', default=NoDefault,
        help='Set the autocall value (0,1,2).')
    ),
    (('-autoindent',), dict(
        action='store_true', dest='AUTOINDENT', default=NoDefault,
        help='Turn on autoindenting.')
    ),
    (('-noautoindent',), dict(
        action='store_false', dest='AUTOINDENT', default=NoDefault,
        help='Turn off autoindenting.')
    ),
    (('-automagic',), dict(
        action='store_true', dest='AUTOMAGIC', default=NoDefault,
        help='Turn on the auto calling of magic commands.')
    ),
    (('-noautomagic',), dict(
        action='store_false', dest='AUTOMAGIC', default=NoDefault,
        help='Turn off the auto calling of magic commands.')
    ),
    (('-autoedit_syntax',), dict(
        action='store_true', dest='AUTOEDIT_SYNTAX', default=NoDefault,
        help='Turn on auto editing of files with syntax errors.')
    ),
    (('-noautoedit_syntax',), dict(
        action='store_false', dest='AUTOEDIT_SYNTAX', default=NoDefault,
        help='Turn off auto editing of files with syntax errors.')
    ),
    (('-banner',), dict(
        action='store_true', dest='DISPLAY_BANNER', default=NoDefault,
        help='Display a banner upon starting IPython.')
    ),
    (('-nobanner',), dict(
        action='store_false', dest='DISPLAY_BANNER', default=NoDefault,
        help="Don't display a banner upon starting IPython.")
    ),
    (('-c',), dict(
        type=str, dest='C', default=NoDefault,
        help="Execute  the  given  command  string.")
    ),
    (('-cache_size',), dict(
        type=int, dest='CACHE_SIZE', default=NoDefault,
        help="Set the size of the output cache.")
    ),
    (('-classic',), dict(
        action='store_true', dest='CLASSIC', default=NoDefault,
        help="Gives IPython a similar feel to the classic Python prompt.")
    ),
    (('-colors',), dict(
        type=str, dest='COLORS', default=NoDefault,
        help="Set the color scheme (NoColor, Linux, and LightBG).")
    ),
    (('-color_info',), dict(
        action='store_true', dest='COLOR_INFO', default=NoDefault,
        help="Enable using colors for info related things.")
    ),
    (('-nocolor_info',), dict(
        action='store_false', dest='COLOR_INFO', default=NoDefault,
        help="Disable using colors for info related things.")
    ),
    (('-confirm_exit',), dict(
        action='store_true', dest='CONFIRM_EXIT', default=NoDefault,
        help="Prompt the user when existing.")
    ),
    (('-noconfirm_exit',), dict(
        action='store_false', dest='CONFIRM_EXIT', default=NoDefault,
        help="Don't prompt the user when existing.")
    ),
    (('-deep_reload',), dict(
        action='store_true', dest='DEEP_RELOAD', default=NoDefault,
        help="Enable deep (recursive) reloading by default.")
    ),
    (('-nodeep_reload',), dict(
        action='store_false', dest='DEEP_RELOAD', default=NoDefault,
        help="Disable deep (recursive) reloading by default.")
    ),
    (('-editor',), dict(
        type=str, dest='EDITOR', default=NoDefault,
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad).")
    ),
    (('-log','-l'), dict(
        action='store_true', dest='LOGSTART', default=NoDefault,
        help="Start logging to the default file (./ipython_log.py).")
    ),
    (('-logfile','-lf'), dict(
        type=str, dest='LOGFILE', default=NoDefault,
        help="Specify the name of your logfile.")
    ),
    (('-logplay','-lp'), dict(
        type=str, dest='LOGPLAY', default=NoDefault,
        help="Re-play a log file and then append to it.")
    ),
    (('-pdb',), dict(
        action='store_true', dest='PDB', default=NoDefault,
        help="Enable auto calling the pdb debugger after every exception.")
    ),
    (('-nopdb',), dict(
        action='store_false', dest='PDB', default=NoDefault,
        help="Disable auto calling the pdb debugger after every exception.")
    ),
    (('-pprint',), dict(
        action='store_true', dest='PPRINT', default=NoDefault,
        help="Enable auto pretty printing of results.")
    ),
    (('-nopprint',), dict(
        action='store_false', dest='PPRINT', default=NoDefault,
        help="Disable auto auto pretty printing of results.")
    ),
    (('-prompt_in1','-pi1'), dict(
        type=str, dest='PROMPT_IN1', default=NoDefault,
        help="Set the main input prompt ('In [\#]: ')")
    ),
    (('-prompt_in2','-pi2'), dict(
        type=str, dest='PROMPT_IN2', default=NoDefault,
        help="Set the secondary input prompt (' .\D.: ')")
    ),
    (('-prompt_out','-po'), dict(
        type=str, dest='PROMPT_OUT', default=NoDefault,
        help="Set the output prompt ('Out[\#]:')")
    ),
    (('-quick',), dict(
        action='store_true', dest='QUICK', default=NoDefault,
        help="Enable quick startup with no config files.")
    ),
    (('-readline',), dict(
        action='store_true', dest='READLINE_USE', default=NoDefault,
        help="Enable readline for command line usage.")
    ),
    (('-noreadline',), dict(
        action='store_false', dest='READLINE_USE', default=NoDefault,
        help="Disable readline for command line usage.")
    ),
    (('-screen_length','-sl'), dict(
        type=int, dest='SCREEN_LENGTH', default=NoDefault,
        help='Number of lines on screen, used to control printing of long strings.')
    ),
    (('-separate_in','-si'), dict(
        type=str, dest='SEPARATE_IN', default=NoDefault,
        help="Separator before input prompts.  Default '\n'.")
    ),
    (('-separate_out','-so'), dict(
        type=str, dest='SEPARATE_OUT', default=NoDefault,
        help="Separator before output prompts.  Default 0 (nothing).")
    ),
    (('-separate_out2','-so2'), dict(
        type=str, dest='SEPARATE_OUT2', default=NoDefault,
        help="Separator after output prompts.  Default 0 (nonight).")
    ),
    (('-nosep',), dict(
        action='store_true', dest='NOSEP', default=NoDefault,
        help="Eliminate all spacing between prompts.")
    ),
    (('-term_title',), dict(
        action='store_true', dest='TERM_TITLE', default=NoDefault,
        help="Enable auto setting the terminal title.")
    ),
    (('-noterm_title',), dict(
        action='store_false', dest='TERM_TITLE', default=NoDefault,
        help="Disable auto setting the terminal title.")
    ),
    (('-xmode',), dict(
        type=str, dest='XMODE', default=NoDefault,
        help="Exception mode ('Plain','Context','Verbose')")
    ),
    # These are only here to get the proper deprecation warnings
    (('-pylab','-wthread','-qthread','-q4thread','-gthread'), dict(
        action='store_true', dest='THREADED_SHELL', default=NoDefault,
        help="These command line flags are deprecated, see the 'gui' magic.")
    ),
)


class IPythonAppCLConfigLoader(IPythonArgParseConfigLoader):

    arguments = cl_args


class IPythonApp(Application):
    name = 'ipython'
    config_file_name = 'ipython_config.py'

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPythonAppCLConfigLoader(
            description=ipython_desc,
            version=release.version)

    def post_load_command_line_config(self):
        """Do actions after loading cl config."""
        clc = self.command_line_config

        # This needs to be set here, the rest are set in pre_construct.
        if hasattr(clc, 'CLASSIC'):
            if clc.CLASSIC: clc.QUICK = 1

        # Display the deprecation warnings about threaded shells
        if hasattr(clc, 'THREADED_SHELL'):
            threaded_shell_warning()
            del clc['THREADED_SHELL']

    def load_file_config(self):
        if hasattr(self.command_line_config, 'QUICK'):
            if self.command_line_config.QUICK:
                self.file_config = Struct()
                return
        super(IPythonApp, self).load_file_config()

    def post_load_file_config(self):
        """Logic goes here."""

    def pre_construct(self):
        config = self.master_config

        if hasattr(config, 'CLASSIC'):
            if config.CLASSIC:
                config.QUICK = 1
                config.CACHE_SIZE = 0
                config.PPRINT = 0
                config.PROMPT_IN1 = '>>> '
                config.PROMPT_IN2 = '... '
                config.PROMPT_OUT = ''
                config.SEPARATE_IN = config.SEPARATE_OUT = config.SEPARATE_OUT2 = ''
                config.COLORS = 'NoColor'
                config.XMODE = 'Plain'

        # All this should be moved to traitlet handlers in InteractiveShell
        # But, currently InteractiveShell doesn't have support for changing
        # these values at runtime.  Once we support that, this should
        # be moved there!!!
        if hasattr(config, 'NOSEP'):
            if config.NOSEP:
                config.SEPARATE_IN = config.SEPARATE_OUT = config.SEPARATE_OUT2 = '0'

    def construct(self):
        # I am a little hesitant to put these into InteractiveShell itself.
        # But that might be the place for them
        sys.path.insert(0, '')
        # add personal ipythondir to sys.path so that users can put things in
        # there for customization
        sys.path.append(os.path.abspath(self.ipythondir))
        
        # Create an InteractiveShell instance
        self.shell = InteractiveShell(
            parent=None,
            config=self.master_config
        )

    def start_app(self):
        self.shell.mainloop()


if __name__ == '__main__':
    app = IPythonApp()
    app.start()