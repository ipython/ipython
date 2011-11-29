.. _configuring_ipython:

===========================================================
Configuring the :command:`ipython` command line application
===========================================================

This section contains information about how to configure the
:command:`ipython` command line application. See the :ref:`configuration
overview <config_overview>` for a more general description of the
configuration system and configuration file format.

The default configuration file for the :command:`ipython` command line application
is :file:`profile_default/ipython_config.py` in your :ref:`IPython directory
<ipython_dir>`. By setting the attributes in this file, you can configure the
application. To create the default config file, run this command::

    $ ipython profile create

Most configuration attributes that this file accepts are associated with classes
that are subclasses of :class:`~IPython.config.configurable.Configurable`.  

Applications themselves are Configurable as well, so we will start with some
application-level config.

Application-level configuration
===============================

Assuming that your configuration file has the following at the top::

    c = get_config()

the following attributes are set application-wide:

terminal IPython-only flags:

:attr:`c.TerminalIPythonApp.display_banner`
    A boolean that determined if the banner is printer when :command:`ipython`
    is started.

:attr:`c.TerminalIPythonApp.classic`
    A boolean that determines if IPython starts in "classic" mode.  In this
    mode, the prompts and everything mimic that of the normal :command:`python`
    shell

:attr:`c.TerminalIPythonApp.nosep`
    A boolean that determines if there should be no blank lines between
    prompts.

:attr:`c.Application.log_level`
    An integer that sets the detail of the logging level during the startup
    of :command:`ipython`.  The default is 30 and the possible values are
    (0, 10, 20, 30, 40, 50).  Higher is quieter and lower is more verbose.
    This can also be set by the name of the logging level, e.g. INFO=20,
    WARN=30.

Some options, such as extensions and startup code, can be set for any
application that starts an
:class:`~IPython.core.interactiveshell.InteractiveShell`. These apps are
subclasses of :class:`~IPython.core.shellapp.InteractiveShellApp`. Since
subclasses inherit configuration, setting a trait of
:attr:`c.InteractiveShellApp` will affect all IPython applications, but if you
want terminal IPython and the QtConsole to have different values, you can set
them via :attr:`c.TerminalIPythonApp` and :attr:`c.IPKernelApp` respectively.


:attr:`c.InteractiveShellApp.extensions`
    A list of strings, each of which is an importable IPython extension. See
    :ref:`extensions_overview` for more details about extensions.

:attr:`c.InteractiveShellApp.exec_lines`
    A list of strings, each of which is Python code that is run in the user's
    namespace after IPython start. These lines can contain full IPython syntax
    with magics, etc.

:attr:`c.InteractiveShellApp.exec_files`
    A list of strings, each of which is the full pathname of a ``.py`` or
    ``.ipy`` file that will be executed as IPython starts. These files are run
    in IPython in the user's namespace. Files with a ``.py`` extension need to
    be pure Python. Files with a ``.ipy`` extension can have custom IPython
    syntax (magics, etc.). These files need to be in the cwd, the ipythondir
    or be absolute paths.

Classes that can be configured
==============================

The following classes can also be configured in the configuration file for
:command:`ipython`:

* :class:`~IPython.core.interactiveshell.InteractiveShell`

* :class:`~IPython.core.prefilter.PrefilterManager`

* :class:`~IPython.core.alias.AliasManager`

To see which attributes of these classes are configurable, please see the
source code for these classes, the class docstrings or the sample
configuration file :mod:`IPython.config.default.ipython_config`.

Example
=======

For those who want to get a quick start, here is a sample
:file:`ipython_config.py` that sets some of the common configuration
attributes::

    # sample ipython_config.py
    c = get_config()

    c.TerminalIPythonApp.display_banner = True
    c.InteractiveShellApp.log_level = 20
    c.InteractiveShellApp.extensions = [
        'myextension'
    ]
    c.InteractiveShellApp.exec_lines = [
        'import numpy',
        'import scipy'
    ]
    c.InteractiveShellApp.exec_files = [
        'mycode.py',
        'fancy.ipy'
    ]
    c.InteractiveShell.autoindent = True
    c.InteractiveShell.colors = 'LightBG'
    c.InteractiveShell.confirm_exit = False
    c.InteractiveShell.deep_reload = True
    c.InteractiveShell.editor = 'nano'
    c.InteractiveShell.xmode = 'Context'
    
    c.PromptManager.in_template  = 'In [\#]: '
    c.PromptManager.in2_template = '   .\D.: '
    c.PromptManager.out_template = 'Out[\#]: '
    c.PromptManager.justify = True

    c.PrefilterManager.multi_line_specials = True

    c.AliasManager.user_aliases = [
     ('la', 'ls -al')
    ]
