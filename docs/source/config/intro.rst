=====================================
Introduction to IPython configuration
=====================================

.. _setting_config:

Setting configurable options
============================

Many of IPython's classes have configurable attributes (see
:doc:`options/index` for the list). These can be
configured in several ways.

Python configuration files
--------------------------

To create the blank configuration files, run::

    ipython profile create [profilename]

If you leave out the profile name, the files will be created for the
``default`` profile (see :ref:`profiles`). These will typically be located in
:file:`~/.ipython/profile_default/`, and will be named
:file:`ipython_config.py`, for historical reasons you may also find files
named with IPython prefix instead of Jupyter:
:file:`ipython_notebook_config.py`, etc. The settings in
:file:`ipython_config.py` apply to all IPython commands.

By default, configuration files are fully featured Python scripts that can
execute arbitrary code, the main usage is to set value on the configuration
object ``c`` which exist in your configuration file.

You can then configure class attributes like this::

    c.InteractiveShell.automagic = False

Be careful with spelling--incorrect names will simply be ignored, with
no error. 

To add to a collection which may have already been defined elsewhere or have
default values, you can use methods like those found on lists, dicts and
sets: append, extend, :meth:`~traitlets.config.LazyConfigValue.prepend` (like
extend, but at the front), add and update (which works both for dicts and
sets)::

    c.InteractiveShellApp.extensions.append('Cython')

.. versionadded:: 2.0
   list, dict and set methods for config values

Example configuration file
``````````````````````````

::

    # sample ipython_config.py

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
    c.InteractiveShell.colors = 'lightbg'
    c.InteractiveShell.xmode = 'Context'
    c.TerminalInteractiveShell.confirm_exit = False
    c.TerminalInteractiveShell.editor = 'nano'

    c.PrefilterManager.multi_line_specials = True

    c.AliasManager.user_aliases = [
     ('la', 'ls -al')
    ]

JSON Configuration files
------------------------

In case where executability of configuration can be problematic, or
configurations need to be modified programmatically, IPython also support a
limited set of functionalities via ``.json`` configuration files. 

You can define most of the configuration options via a JSON object whose
hierarchy represents the value you would normally set on the ``c`` object of
``.py`` configuration files. The following ``ipython_config.json`` file::

    {
        "InteractiveShell": {
            "colors": "lightbg",
        },
        "InteractiveShellApp": {
            "extensions": [
                "myextension"
            ]
        },
        "TerminalInteractiveShell": {
            "editor": "nano"
        }
    }

Is equivalent to the following ``ipython_config.py``::

    c.InteractiveShell.colors = 'lightbg'
    c.InteractiveShellApp.extensions = [
        'myextension'
    ]
    c.TerminalInteractiveShell.editor = 'nano'


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
    jupyter notebook --help
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

.. _configure_start_ipython:

Running IPython from Python
----------------------------

If you are using :ref:`embedding` to start IPython from a normal 
python file, you can set configuration options the same way as in a 
config file by creating a traitlets :class:`Config` object and passing it to 
start_ipython like in the example below.

.. literalinclude:: ../../../examples/Embedding/start_ipython_config.py
    :language: python

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

To see where IPython is looking for the IPython directory, use the command
``ipython locate``, or the Python function :func:`IPython.paths.get_ipython_dir`.


Systemwide configuration
========================

It can be useful to deploy systemwide ipython or ipykernel configuration
when managing environment for many users. At startup time IPython and
IPykernel will search for configuration file in multiple systemwide
locations, mainly:

  - ``/etc/ipython/``
  - ``/usr/local/etc/ipython/``

When the global install is a standalone python distribution it may also
search in distribution specific location, for example:

  - ``$ANACONDA_LOCATION/etc/ipython/``

In those locations, Terminal IPython will look for a file called
``ipython_config.py`` and ``ipython_config.json``, ipykernel will look for
``ipython_kernel_config.py`` and ``ipython_kernel.json``.

Configuration files are loaded in order and merged with configuration on
later location taking precedence on earlier locations (that is to say a user
can overwrite a systemwide configuration option).

You can see all locations in which IPython is looking for configuration files
by starting ipython in debug mode::

    $ ipython --debug -c 'exit()'

Identically with ipykernel though the command is currently blocking until
this process is killed with ``Ctrl-\``::
 
    $ python -m ipykernel --debug
