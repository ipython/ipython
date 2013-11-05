=====================================
Introduction to IPython configuration
=====================================

.. _setting_config:

Setting configurable options
============================

Many of IPython's classes have configurable attributes (see
:doc:`options/index` for the list). These can be
configured in several ways.

Python config files
-------------------

To create the blank config files, run::

    ipython profile create [profilename]

If you leave out the profile name, the files will be created for the
``default`` profile (see :ref:`profiles`). These will typically be
located in :file:`~/.ipython/profile_default/`, and will be named
:file:`ipython_config.py`, :file:`ipython_notebook_config.py`, etc.
The settings in :file:`ipython_config.py` apply to all IPython commands.

The files typically start by getting the root config object::

    c = get_config()

You can then configure class attributes like this::

    c.InteractiveShell.automagic = False

Be careful with spelling--incorrect names will simply be ignored, with
no error.

To add to a collection which may have already been defined elsewhere,
you can use methods like those found on lists, dicts and sets: append,
extend, :meth:`~IPython.config.loader.LazyConfigValue.prepend` (like
extend, but at the front), add and update (which works both for dicts
and sets)::

    c.InteractiveShellApp.extensions.append('rmagic')

.. versionadded:: 2.0
   list, dict and set methods for config values

Example config file
```````````````````

::

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


Command line arguments
----------------------

Every configurable value can be set from the command line, using this
syntax::

    ipython --ClassName.attribute=value

Many frequently used options have short aliases and flags, such as
``--matplotlib`` (to integrate with a matplotlib GUI event loop) or
``--pdb`` (automatic post-mortem debugging of exceptions).

To see all of these abbreviated options, run::

    ipython --help
    ipython notebook --help
    # etc.

Options specified at the command line, in either format, override
options set in a configuration file.

The config magic
----------------

You can also modify config from inside IPython, using a magic command::

    %config IPCompleter.greedy = True

At present, this only affects the current session - changes you make to
config are not saved anywhere. Also, some options are only read when
IPython starts, so they can't be changed like this.

.. _profiles:

Profiles
========

IPython can use multiple profiles, with separate configuration and
history. By default, if you don't specify a profile, IPython always runs
in the ``default`` profile. To use a new profile::

    ipython profile create foo   # create the profile foo
    ipython --profile=foo        # start IPython using the new profile

Profiles are typically stored in :ref:`ipythondir`, but you can also keep
a profile in the current working directory, for example to distribute it
with a project. To find a profile directory on the filesystem::

    ipython locate profile foo

.. _ipythondir:

The IPython directory
=====================

IPython stores its files---config, command history and extensions---in
the directory :file:`~/.ipython/` by default.

.. envvar:: IPYTHONDIR

   If set, this environment variable should be the path to a directory,
   which IPython will use for user data. IPython will create it if it
   does not exist.

.. option:: --ipython-dir=<path>

   This command line option can also be used to override the default
   IPython directory.
