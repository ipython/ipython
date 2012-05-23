"""Magic functions for InteractiveShell.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#  Copyright (C) 2001 Fernando Perez <fperez@colorado.edu>
#  Copyright (C) 2008 The IPython Development Team

#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import os
import re
import sys
from pprint import pformat

# Our own packages
from IPython.config.application import Application
from IPython.core import oinspect
from IPython.core import page
from IPython.core.error import UsageError
from IPython.core.magic import (Magics, compress_dhist,
                                register_magics, line_magic)
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.io import file_read, nlprint
from IPython.utils.path import get_py_filename, unquote_filename
from IPython.utils.process import abbrev_cwd
from IPython.utils.terminal import set_term_title
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@register_magics
class LoggingMagics(Magics):
    """Magics related to all logging machinery."""

    @line_magic
    def logstart(self, parameter_s=''):
        """Start logging anywhere in a session.

        %logstart [-o|-r|-t] [log_name [log_mode]]

        If no name is given, it defaults to a file named 'ipython_log.py' in your
        current directory, in 'rotate' mode (see below).

        '%logstart name' saves to file 'name' in 'backup' mode.  It saves your
        history up to that point and then continues logging.

        %logstart takes a second optional parameter: logging mode. This can be one
        of (note that the modes are given unquoted):\\
          append: well, that says it.\\
          backup: rename (if exists) to name~ and start name.\\
          global: single logfile in your home dir, appended to.\\
          over  : overwrite existing log.\\
          rotate: create rotating logs name.1~, name.2~, etc.

        Options:

          -o: log also IPython's output.  In this mode, all commands which
          generate an Out[NN] prompt are recorded to the logfile, right after
          their corresponding input line.  The output lines are always
          prepended with a '#[Out]# ' marker, so that the log remains valid
          Python code.

          Since this marker is always the same, filtering only the output from
          a log is very easy, using for example a simple awk call::

            awk -F'#\\[Out\\]# ' '{if($2) {print $2}}' ipython_log.py

          -r: log 'raw' input.  Normally, IPython's logs contain the processed
          input, so that user lines are logged in their final form, converted
          into valid Python.  For example, %Exit is logged as
          _ip.magic("Exit").  If the -r flag is given, all input is logged
          exactly as typed, with no transformations applied.

          -t: put timestamps before each input line logged (these are put in
          comments)."""

        opts,par = self.parse_options(parameter_s,'ort')
        log_output = 'o' in opts
        log_raw_input = 'r' in opts
        timestamp = 't' in opts

        logger = self.shell.logger

        # if no args are given, the defaults set in the logger constructor by
        # ipython remain valid
        if par:
            try:
                logfname,logmode = par.split()
            except:
                logfname = par
                logmode = 'backup'
        else:
            logfname = logger.logfname
            logmode = logger.logmode
        # put logfname into rc struct as if it had been called on the command
        # line, so it ends up saved in the log header Save it in case we need
        # to restore it...
        old_logfile = self.shell.logfile
        if logfname:
            logfname = os.path.expanduser(logfname)
        self.shell.logfile = logfname

        loghead = '# IPython log file\n\n'
        try:
            logger.logstart(logfname, loghead, logmode, log_output, timestamp,
                            log_raw_input)
        except:
            self.shell.logfile = old_logfile
            warn("Couldn't start log: %s" % sys.exc_info()[1])
        else:
            # log input history up to this point, optionally interleaving
            # output if requested

            if timestamp:
                # disable timestamping for the previous history, since we've
                # lost those already (no time machine here).
                logger.timestamp = False

            if log_raw_input:
                input_hist = self.shell.history_manager.input_hist_raw
            else:
                input_hist = self.shell.history_manager.input_hist_parsed

            if log_output:
                log_write = logger.log_write
                output_hist = self.shell.history_manager.output_hist
                for n in range(1,len(input_hist)-1):
                    log_write(input_hist[n].rstrip() + '\n')
                    if n in output_hist:
                        log_write(repr(output_hist[n]),'output')
            else:
                logger.log_write('\n'.join(input_hist[1:]))
                logger.log_write('\n')
            if timestamp:
                # re-enable timestamping
                logger.timestamp = True

            print ('Activating auto-logging. '
                   'Current session state plus future input saved.')
            logger.logstate()

    @line_magic
    def logstop(self, parameter_s=''):
        """Fully stop logging and close log file.

        In order to start logging again, a new %logstart call needs to be made,
        possibly (though not necessarily) with a new filename, mode and other
        options."""
        self.logger.logstop()

    @line_magic
    def logoff(self, parameter_s=''):
        """Temporarily stop logging.

        You must have previously started logging."""
        self.shell.logger.switch_log(0)

    @line_magic
    def logon(self, parameter_s=''):
        """Restart logging.

        This function is for restarting logging which you've temporarily
        stopped with %logoff. For starting logging for the first time, you
        must use the %logstart function, which allows you to specify an
        optional log filename."""

        self.shell.logger.switch_log(1)

    @line_magic
    def logstate(self, parameter_s=''):
        """Print the status of the logging system."""

        self.shell.logger.logstate()


@register_magics
class ExtensionsMagics(Magics):
    """Magics to manage the IPython extensions system."""

    @line_magic
    def install_ext(self, parameter_s=''):
        """Download and install an extension from a URL, e.g.::

            %install_ext https://bitbucket.org/birkenfeld/ipython-physics/raw/d1310a2ab15d/physics.py

        The URL should point to an importable Python module - either a .py file
        or a .zip file.

        Parameters:

          -n filename : Specify a name for the file, rather than taking it from
                        the URL.
        """
        opts, args = self.parse_options(parameter_s, 'n:')
        try:
            filename = self.shell.extension_manager.install_extension(args,
                                                                 opts.get('n'))
        except ValueError as e:
            print e
            return

        filename = os.path.basename(filename)
        print "Installed %s. To use it, type:" % filename
        print "  %%load_ext %s" % os.path.splitext(filename)[0]


    @line_magic
    def load_ext(self, module_str):
        """Load an IPython extension by its module name."""
        return self.shell.extension_manager.load_extension(module_str)

    @line_magic
    def unload_ext(self, module_str):
        """Unload an IPython extension by its module name."""
        self.shell.extension_manager.unload_extension(module_str)

    @line_magic
    def reload_ext(self, module_str):
        """Reload an IPython extension by its module name."""
        self.shell.extension_manager.reload_extension(module_str)


@register_magics
class PylabMagics(Magics):
    """Magics related to matplotlib's pylab support"""

    @skip_doctest
    @line_magic
    def pylab(self, parameter_s=''):
        """Load numpy and matplotlib to work interactively.

        %pylab [GUINAME]

        This function lets you activate pylab (matplotlib, numpy and
        interactive support) at any point during an IPython session.

        It will import at the top level numpy as np, pyplot as plt, matplotlib,
        pylab and mlab, as well as all names from numpy and pylab.

        If you are using the inline matplotlib backend for embedded figures,
        you can adjust its behavior via the %config magic::

            # enable SVG figures, necessary for SVG+XHTML export in the qtconsole
            In [1]: %config InlineBackend.figure_format = 'svg'

            # change the behavior of closing all figures at the end of each
            # execution (cell), or allowing reuse of active figures across
            # cells:
            In [2]: %config InlineBackend.close_figures = False

        Parameters
        ----------
        guiname : optional
          One of the valid arguments to the %gui magic ('qt', 'wx', 'gtk',
          'osx' or 'tk').  If given, the corresponding Matplotlib backend is
          used, otherwise matplotlib's default (which you can override in your
          matplotlib config file) is used.

        Examples
        --------
        In this case, where the MPL default is TkAgg::

            In [2]: %pylab

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: TkAgg
            For more information, type 'help(pylab)'.

        But you can explicitly request a different backend::

            In [3]: %pylab qt

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: Qt4Agg
            For more information, type 'help(pylab)'.
        """

        if Application.initialized():
            app = Application.instance()
            try:
                import_all_status = app.pylab_import_all
            except AttributeError:
                import_all_status = True
        else:
            import_all_status = True

        self.shell.enable_pylab(parameter_s, import_all=import_all_status)


@register_magics
class DeprecatedMagics(Magics):
    """Magics slated for later removal."""

    @line_magic
    def install_profiles(self, parameter_s=''):
        """%install_profiles has been deprecated."""
        print '\n'.join([
            "%install_profiles has been deprecated.",
            "Use `ipython profile list` to view available profiles.",
            "Requesting a profile with `ipython profile create <name>`",
            "or `ipython --profile=<name>` will start with the bundled",
            "profile of that name if it exists."
        ])

    @line_magic
    def install_default_config(self, parameter_s=''):
        """%install_default_config has been deprecated."""
        print '\n'.join([
            "%install_default_config has been deprecated.",
            "Use `ipython profile create <name>` to initialize a profile",
            "with the default config files.",
            "Add `--reset` to overwrite already existing config files with defaults."
        ])
