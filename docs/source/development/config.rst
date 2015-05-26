.. _config_overview:

============================================
Overview of the IPython configuration system
============================================

This section describes the IPython configuration system. This is based on
:mod:`traitlets.config`; see that documentation for more information
about the overall architecture.

Configuration file location
===========================

So where should you put your configuration files? IPython uses "profiles" for
configuration, and by default, all profiles will be stored in the so called
"IPython directory". The location of this directory is determined by the
following algorithm:

* If the ``ipython-dir`` command line flag is given, its value is used.

* If not, the value returned by :func:`IPython.paths.get_ipython_dir`
  is used. This function will first look at the :envvar:`IPYTHONDIR`
  environment variable and then default to :file:`~/.ipython`.
  Historical support for the :envvar:`IPYTHON_DIR` environment variable will
  be removed in a future release.

For most users, the configuration directory will be :file:`~/.ipython`.

Previous versions of IPython on Linux would use the XDG config directory,
creating :file:`~/.config/ipython` by default. We have decided to go
back to :file:`~/.ipython` for consistency among systems. IPython will
issue a warning if it finds the XDG location, and will move it to the new
location if there isn't already a directory there.

Once the location of the IPython directory has been determined, you need to know
which profile you are using. For users with a single configuration, this will
simply be 'default', and will be located in 
:file:`<IPYTHONDIR>/profile_default`.

The next thing you need to know is what to call your configuration file. The
basic idea is that each application has its own default configuration filename.
The default named used by the :command:`ipython` command line program is
:file:`ipython_config.py`, and *all* IPython applications will use this file.
Other applications, such as the parallel :command:`ipcluster` scripts or the
QtConsole will load their own config files *after* :file:`ipython_config.py`. To
load a particular configuration file instead of the default, the name can be
overridden by the ``config_file`` command line flag.

To generate the default configuration files, do::

    $ ipython profile create

and you will have a default :file:`ipython_config.py` in your IPython directory
under :file:`profile_default`. If you want the default config files for the
:mod:`IPython.parallel` applications, add ``--parallel`` to the end of the
command-line args.


Locating these files
--------------------

From the command-line, you can quickly locate the IPYTHONDIR or a specific
profile with:

.. sourcecode:: bash

    $ ipython locate
    /home/you/.ipython
    
    $ ipython locate profile foo
    /home/you/.ipython/profile_foo

These map to the utility functions: :func:`IPython.utils.path.get_ipython_dir`
and :func:`IPython.utils.path.locate_profile` respectively.


.. _profiles_dev:

Profiles
========

A profile is a directory containing configuration and runtime files, such as
logs, connection info for the parallel apps, and your IPython command history.

The idea is that users often want to maintain a set of configuration files for
different purposes: one for doing numerical computing with NumPy and SciPy and
another for doing symbolic computing with SymPy. Profiles make it easy to keep a
separate configuration files, logs, and histories for each of these purposes.

Let's start by showing how a profile is used:

.. code-block:: bash

    $ ipython --profile=sympy

This tells the :command:`ipython` command line program to get its configuration
from the "sympy" profile. The file names for various profiles do not change. The
only difference is that profiles are named in a special way. In the case above,
the "sympy" profile means looking for :file:`ipython_config.py` in :file:`<IPYTHONDIR>/profile_sympy`.

The general pattern is this: simply create a new profile with:

.. code-block:: bash

    $ ipython profile create <name>

which adds a directory called ``profile_<name>`` to your IPython directory. Then
you can load this profile by adding ``--profile=<name>`` to your command line
options. Profiles are supported by all IPython applications.

IPython ships with some sample profiles in :file:`IPython/config/profile`. If
you create profiles with the name of one of our shipped profiles, these config
files will be copied over instead of starting with the automatically generated
config files.

IPython extends the config loader for Python files so that you can inherit
config from another profile. To do this, use a line like this in your Python
config file:

.. sourcecode:: python

    load_subconfig('ipython_config.py', profile='default')
