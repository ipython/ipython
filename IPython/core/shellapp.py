#!/usr/bin/env python
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

import os
import sys

from IPython.config.application import boolean_flag
from IPython.config.configurable import Configurable
from IPython.config.loader import Config
from IPython.utils.path import filefind
from IPython.utils.traitlets import Unicode, Instance, List

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


# it's possible we don't want short aliases for *all* of these:
shell_aliases = dict(
    autocall='InteractiveShell.autocall',
    cache_size='InteractiveShell.cache_size',
    colors='InteractiveShell.colors',
    logfile='InteractiveShell.logfile',
    log_append='InteractiveShell.logappend',
    c='InteractiveShellApp.code_to_run',
    ext='InteractiveShellApp.extra_extension',
)

#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------

class InteractiveShellApp(Configurable):
    """A Mixin for applications that start InteractiveShell instances.
    
    Provides configurables for loading extensions and executing files
    as part of configuring a Shell environment.
    
    Provides init_extensions() and init_code() methods, to be called
    after init_shell(), which must be implemented by subclasses.
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
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def init_shell(self):
        raise NotImplementedError("Override in subclasses")
    
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

