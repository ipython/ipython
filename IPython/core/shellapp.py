# encoding: utf-8
"""
A mixin for :class:`~IPython.core.application.Application` classes that
launch InteractiveShell instances, load extensions, etc.

Authors
-------

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

import glob
import os
import sys

from IPython.config.application import boolean_flag
from IPython.config.configurable import Configurable
from IPython.config.loader import Config
from IPython.core import pylabtools
from IPython.utils import py3compat
from IPython.utils.contexts import preserve_keys
from IPython.utils.path import filefind
from IPython.utils.traitlets import (
    Unicode, Instance, List, Bool, CaselessStrEnum
)

#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

shell_flags = {}

addflag = lambda *args: shell_flags.update(boolean_flag(*args))
addflag('autoindent', 'InteractiveShell.autoindent',
        'Turn on autoindenting.', 'Turn off autoindenting.'
)
addflag('automagic', 'InteractiveShell.automagic',
        """Turn on the auto calling of magic commands. Type %%magic at the
        IPython  prompt  for  more information.""",
        'Turn off the auto calling of magic commands.'
)
addflag('pdb', 'InteractiveShell.pdb',
    "Enable auto calling the pdb debugger after every exception.",
    "Disable auto calling the pdb debugger after every exception."
)
# pydb flag doesn't do any config, as core.debugger switches on import,
# which is before parsing.  This just allows the flag to be passed.
shell_flags.update(dict(
    pydb = ({},
        """Use the third party 'pydb' package as debugger, instead of pdb.
        Requires that pydb is installed."""
    )
))
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
    interactively for testing.""",
    "Disable using colors for info related things."
)
addflag('deep-reload', 'InteractiveShell.deep_reload',
    """Enable deep (recursive) reloading by default. IPython can use the
    deep_reload module which reloads changes in modules recursively (it
    replaces the reload() function, so you don't need to change anything to
    use it). deep_reload() forces a full reload of modules whose code may
    have changed, which the default reload() function does not.  When
    deep_reload is off, IPython will use the normal reload(), but
    deep_reload will still be available as dreload(). This feature is off
    by default [which means that you have both normal reload() and
    dreload()].""",
    "Disable deep (recursive) reloading by default."
)
nosep_config = Config()
nosep_config.InteractiveShell.separate_in = ''
nosep_config.InteractiveShell.separate_out = ''
nosep_config.InteractiveShell.separate_out2 = ''

shell_flags['nosep']=(nosep_config, "Eliminate all spacing between prompts.")
shell_flags['pylab'] = (
    {'InteractiveShellApp' : {'pylab' : 'auto'}},
    """Pre-load matplotlib and numpy for interactive use with
    the default matplotlib backend."""
)

# it's possible we don't want short aliases for *all* of these:
shell_aliases = dict(
    autocall='InteractiveShell.autocall',
    colors='InteractiveShell.colors',
    logfile='InteractiveShell.logfile',
    logappend='InteractiveShell.logappend',
    c='InteractiveShellApp.code_to_run',
    m='InteractiveShellApp.module_to_run',
    ext='InteractiveShellApp.extra_extension',
    gui='InteractiveShellApp.gui',
    pylab='InteractiveShellApp.pylab',
)
shell_aliases['cache-size'] = 'InteractiveShell.cache_size'

#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------

class InteractiveShellApp(Configurable):
    """A Mixin for applications that start InteractiveShell instances.
    
    Provides configurables for loading extensions and executing files
    as part of configuring a Shell environment.

    The following methods should be called by the :meth:`initialize` method
    of the subclass:

      - :meth:`init_path`
      - :meth:`init_shell` (to be implemented by the subclass)
      - :meth:`init_gui_pylab`
      - :meth:`init_extensions`
      - :meth:`init_code`
    """
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
    
    # Extensions that are always loaded (not configurable)
    default_extensions = List(Unicode, [u'storemagic'], config=False)

    exec_files = List(Unicode, config=True,
        help="""List of files to run at IPython startup."""
    )
    file_to_run = Unicode('', config=True,
        help="""A file to be run""")

    exec_lines = List(Unicode, config=True,
        help="""lines of code to run at IPython startup."""
    )
    code_to_run = Unicode('', config=True,
        help="Execute the given command string."
    )
    module_to_run = Unicode('', config=True,
        help="Run the module as a script."
    )
    gui = CaselessStrEnum(('qt', 'wx', 'gtk', 'glut', 'pyglet', 'osx'), config=True,
        help="Enable GUI event loop integration ('qt', 'wx', 'gtk', 'glut', 'pyglet', 'osx')."
    )
    pylab = CaselessStrEnum(['tk', 'qt', 'wx', 'gtk', 'osx', 'inline', 'auto'],
        config=True,
        help="""Pre-load matplotlib and numpy for interactive use,
        selecting a particular matplotlib backend and loop integration.
        """
    )
    pylab_import_all = Bool(True, config=True,
        help="""If true, an 'import *' is done from numpy and pylab,
        when using pylab"""
    )
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def init_path(self):
        """Add current working directory, '', to sys.path"""
        if sys.path[0] != '':
            sys.path.insert(0, '')

    def init_shell(self):
        raise NotImplementedError("Override in subclasses")

    def init_gui_pylab(self):
        """Enable GUI event loop integration, taking pylab into account."""
        if self.gui or self.pylab:
            shell = self.shell
            try:
                if self.pylab:
                    gui, backend = pylabtools.find_gui_and_backend(self.pylab)
                    self.log.info("Enabling GUI event loop integration, "
                              "toolkit=%s, pylab=%s" % (gui, self.pylab))
                    shell.enable_pylab(gui, import_all=self.pylab_import_all, welcome_message=True)
                else:
                    self.log.info("Enabling GUI event loop integration, "
                                  "toolkit=%s" % self.gui)
                    shell.enable_gui(self.gui)
            except Exception:
                self.log.warn("GUI event loop or pylab initialization failed")
                self.shell.showtraceback()

    def init_extensions(self):
        """Load all IPython extensions in IPythonApp.extensions.

        This uses the :meth:`ExtensionManager.load_extensions` to load all
        the extensions listed in ``self.extensions``.
        """
        try:
            self.log.debug("Loading IPython extensions...")
            extensions = self.default_extensions + self.extensions
            for ext in extensions:
                try:
                    self.log.info("Loading IPython extension: %s" % ext)
                    self.shell.extension_manager.load_extension(ext)
                except:
                    self.log.warn("Error in loading extension: %s" % ext +
                        "\nCheck your config files in %s" % self.profile_dir.location
                    )
                    self.shell.showtraceback()
        except:
            self.log.warn("Unknown error in loading extensions:")
            self.shell.showtraceback()

    def init_code(self):
        """run the pre-flight code, specified via exec_lines"""
        self._run_startup_files()
        self._run_exec_lines()
        self._run_exec_files()
        self._run_cmd_line_code()
        self._run_module()
        
        # flush output, so itwon't be attached to the first cell
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Hide variables defined here from %who etc.
        self.shell.user_ns_hidden.update(self.shell.user_ns)

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
        try:
            full_filename = filefind(fname, [u'.', self.ipython_dir])
        except IOError as e:
            self.log.warn("File not found: %r"%fname)
            return
        # Make sure that the running script gets a proper sys.argv as if it
        # were run from a system shell.
        save_argv = sys.argv
        sys.argv = [full_filename] + self.extra_args[1:]
        # protect sys.argv from potential unicode strings on Python 2:
        if not py3compat.PY3:
            sys.argv = [ py3compat.cast_bytes(a) for a in sys.argv ]
        try:
            if os.path.isfile(full_filename):
                self.log.info("Running file in user namespace: %s" %
                              full_filename)
                # Ensure that __file__ is always defined to match Python
                # behavior.
                with preserve_keys(self.shell.user_ns, '__file__'):
                    self.shell.user_ns['__file__'] = fname
                    if full_filename.endswith('.ipy'):
                        self.shell.safe_execfile_ipy(full_filename)
                    else:
                        # default to python, even without extension
                        self.shell.safe_execfile(full_filename,
                                                 self.shell.user_ns)
        finally:
            sys.argv = save_argv

    def _run_startup_files(self):
        """Run files from profile startup directory"""
        startup_dir = self.profile_dir.startup_dir
        startup_files = glob.glob(os.path.join(startup_dir, '*.py'))
        startup_files += glob.glob(os.path.join(startup_dir, '*.ipy'))
        if not startup_files:
            return
        
        self.log.debug("Running startup files from %s...", startup_dir)
        try:
            for fname in sorted(startup_files):
                self._exec_file(fname)
        except:
            self.log.warn("Unknown error in handling startup files:")
            self.shell.showtraceback()

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

    def _run_module(self):
        """Run module specified at the command-line."""
        if self.module_to_run:
            # Make sure that the module gets a proper sys.argv as if it were
            # run using `python -m`.
            save_argv = sys.argv
            sys.argv = [sys.executable] + self.extra_args
            try:
                self.shell.safe_run_module(self.module_to_run,
                                           self.shell.user_ns)
            finally:
                sys.argv = save_argv
