.. _config_overview:

============================================
Overview of the IPython configuration system
============================================

This section describes the IPython configuration system. 

The main concepts
=================

There are a number of abstractions that the IPython configuration system uses.
Each of these abstractions is represented by a Python class.

Configuration object: :class:`~IPython.config.loader.Config`
    A configuration object is a simple dictionary-like class that holds
    configuration attributes and sub-configuration objects. These classes
    support dotted attribute style access (``cfg.Foo.bar``) in addition to the
    regular dictionary style access (``cfg['Foo']['bar']``).
    The Config object is a wrapper around a simple dictionary with some convenience methods,
    such as merging and automatic section creation.

Application: :class:`~IPython.config.application.Application`
    An application is a process that does a specific job. The most obvious
    application is the :command:`ipython` command line program. Each
    application reads *one or more* configuration files and a single set of
    command line options
    and then produces a master configuration object for the application. This
    configuration object is then passed to the configurable objects that the
    application creates. These configurable objects implement the actual logic
    of the application and know how to configure themselves given the
    configuration object.
    
    Applications always have a `log` attribute that is a configured Logger.
    This allows centralized logging configuration per-application.

Configurable: :class:`~IPython.config.configurable.Configurable`
    A configurable is a regular Python class that serves as a base class for
    all main classes in an application. The
    :class:`~IPython.config.configurable.Configurable` base class is
    lightweight and only does one things.

    This :class:`~IPython.config.configurable.Configurable` is a subclass
    of :class:`~IPython.utils.traitlets.HasTraits` that knows how to configure
    itself. Class level traits with the metadata ``config=True`` become
    values that can be configured from the command line and configuration
    files.
    
    Developers create :class:`~IPython.config.configurable.Configurable`
    subclasses that implement all of the logic in the application. Each of
    these subclasses has its own configuration information that controls how
    instances are created.

Singletons: :class:`~IPython.config.configurable.SingletonConfigurable`
    Any object for which there is a single canonical instance. These are
    just like Configurables, except they have a class method 
    :meth:`~IPython.config.configurable.SingletonConfigurable.instance`,
    that returns the current active instance (or creates one if it
    does not exist).  Examples of singletons include
    :class:`~IPython.config.application.Application`s and
    :class:`~IPython.core.interactiveshell.InteractiveShell`.  This lets
    objects easily connect to the current running Application without passing
    objects around everywhere.  For instance, to get the current running 
    Application instance, simply do: ``app = Application.instance()``.


.. note::

    Singletons are not strictly enforced - you can have many instances
    of a given singleton class, but the :meth:`instance` method will always
    return the same one.

Having described these main concepts, we can now state the main idea in our
configuration system: *"configuration" allows the default values of class
attributes to be controlled on a class by class basis*. Thus all instances of
a given class are configured in the same way. Furthermore, if two instances
need to be configured differently, they need to be instances of two different
classes. While this model may seem a bit restrictive, we have found that it
expresses most things that need to be configured extremely well. However, it
is possible to create two instances of the same class that have different
trait values. This is done by overriding the configuration.

Now, we show what our configuration objects and files look like.

Configuration objects and files
===============================

A configuration object is little more than a wrapper around a dictionary.
A configuration *file* is simply a mechanism for producing that object.
The main IPython configuration file is a plain Python script,
which can perform extensive logic to populate the config object.
IPython 2.0 introduces a JSON configuration file,
which is just a direct JSON serialization of the config dictionary,
which is easily processed by external software.

When both Python and JSON configuration file are present, both will be loaded,
with JSON configuration having higher priority.

Python configuration Files
--------------------------

A Python configuration file is a pure Python file that populates a configuration object.
This configuration object is a :class:`~IPython.config.loader.Config` instance.
While in a configuration file, to get a reference to this object, simply call the :func:`get_config`
function, which is available in the global namespace of the script.

Here is an example of a super simple configuration file that does nothing::

    c = get_config()

Once you get a reference to the configuration object, you simply set
attributes on it.  All you have to know is:

* The name of the class to configure.
* The name of the attribute.
* The type of each attribute.

The answers to these questions are provided by the various
:class:`~IPython.config.configurable.Configurable` subclasses that an
application uses. Let's look at how this would work for a simple configurable
subclass::

    # Sample configurable:
    from IPython.config.configurable import Configurable
    from IPython.utils.traitlets import Int, Float, Unicode, Bool
    
    class MyClass(Configurable):
        name = Unicode(u'defaultname', config=True)
        ranking = Int(0, config=True)
        value = Float(99.0)
        # The rest of the class implementation would go here..

In this example, we see that :class:`MyClass` has three attributes, two
of which (``name``, ``ranking``) can be configured.  All of the attributes
are given types and default values.  If a :class:`MyClass` is instantiated,
but not configured, these default values will be used.  But let's see how
to configure this class in a configuration file::

    # Sample config file
    c = get_config()
    
    c.MyClass.name = 'coolname'
    c.MyClass.ranking = 10

After this configuration file is loaded, the values set in it will override
the class defaults anytime a :class:`MyClass` is created.  Furthermore,
these attributes will be type checked and validated anytime they are set.
This type checking is handled by the :mod:`IPython.utils.traitlets` module,
which provides the :class:`Unicode`, :class:`Int` and :class:`Float` types.
In addition to these traitlets, the :mod:`IPython.utils.traitlets` provides
traitlets for a number of other types.

.. note::

    Underneath the hood, the :class:`Configurable` base class is a subclass of
    :class:`IPython.utils.traitlets.HasTraits`. The
    :mod:`IPython.utils.traitlets` module is a lightweight version of
    :mod:`enthought.traits`. Our implementation is a pure Python subset
    (mostly API compatible) of :mod:`enthought.traits` that does not have any
    of the automatic GUI generation capabilities. Our plan is to achieve 100%
    API compatibility to enable the actual :mod:`enthought.traits` to
    eventually be used instead. Currently, we cannot use
    :mod:`enthought.traits` as we are committed to the core of IPython being
    pure Python.

It should be very clear at this point what the naming convention is for 
configuration attributes::

    c.ClassName.attribute_name = attribute_value

Here, ``ClassName`` is the name of the class whose configuration attribute you
want to set, ``attribute_name`` is the name of the attribute you want to set
and ``attribute_value`` the the value you want it to have. The ``ClassName``
attribute of ``c`` is not the actual class, but instead is another
:class:`~IPython.config.loader.Config` instance.

.. note::

    The careful reader may wonder how the ``ClassName`` (``MyClass`` in
    the above example) attribute of the configuration object ``c`` gets
    created. These attributes are created on the fly by the
    :class:`~IPython.config.loader.Config` instance, using a simple naming
    convention. Any attribute of a :class:`~IPython.config.loader.Config`
    instance whose name begins with an uppercase character is assumed to be a
    sub-configuration and a new empty :class:`~IPython.config.loader.Config`
    instance is dynamically created for that attribute. This allows deeply
    hierarchical information created easily (``c.Foo.Bar.value``) on the fly.

JSON configuration Files
------------------------

A JSON configuration file is simply a file that contains a
:class:`~IPython.config.loader.Config` dictionary serialized to JSON.
A JSON configuration file has the same base name as a Python configuration file,
but with a .json extension.

Configuration described in previous section could be written as follows in a
JSON configuration file:

.. sourcecode:: json

    {
      "version": "1.0",
      "MyClass": {
        "name": "coolname",
        "ranking": 10
      }
    }

JSON configuration files can be more easily generated or processed by programs
or other languages.


Configuration files inheritance
===============================

.. note::

    This section only apply to Python configuration files.

Let's say you want to have different configuration files for various purposes.
Our configuration system makes it easy for one configuration file to inherit
the information in another configuration file. The :func:`load_subconfig`
command can be used in a configuration file for this purpose. Here is a simple
example that loads all of the values from the file :file:`base_config.py`::

    # base_config.py
    c = get_config()
    c.MyClass.name = 'coolname'
    c.MyClass.ranking = 100

into the configuration file :file:`main_config.py`::

    # main_config.py
    c = get_config()
    
    # Load everything from base_config.py
    load_subconfig('base_config.py')
    
    # Now override one of the values
    c.MyClass.name = 'bettername'

In a situation like this the :func:`load_subconfig` makes sure that the
search path for sub-configuration files is inherited from that of the parent.
Thus, you can typically put the two in the same directory and everything will
just work.

You can also load configuration files by profile, for instance:

.. sourcecode:: python

    load_subconfig('ipython_config.py', profile='default')

to inherit your default configuration as a starting point.


Class based configuration inheritance
=====================================

There is another aspect of configuration where inheritance comes into play.
Sometimes, your classes will have an inheritance hierarchy that you want
to be reflected in the configuration system.  Here is a simple example::

    from IPython.config.configurable import Configurable
    from IPython.utils.traitlets import Int, Float, Unicode, Bool
    
    class Foo(Configurable):
        name = Unicode(u'fooname', config=True)
        value = Float(100.0, config=True)
    
    class Bar(Foo):
        name = Unicode(u'barname', config=True)
        othervalue = Int(0, config=True)

Now, we can create a configuration file to configure instances of :class:`Foo`
and :class:`Bar`::

    # config file
    c = get_config()
    
    c.Foo.name = u'bestname'
    c.Bar.othervalue = 10

This class hierarchy and configuration file accomplishes the following:

* The default value for :attr:`Foo.name` and :attr:`Bar.name` will be
  'bestname'.  Because :class:`Bar` is a :class:`Foo` subclass it also
  picks up the configuration information for :class:`Foo`.
* The default value for :attr:`Foo.value` and :attr:`Bar.value` will be
  ``100.0``, which is the value specified as the class default.
* The default value for :attr:`Bar.othervalue` will be 10 as set in the
  configuration file.  Because :class:`Foo` is the parent of :class:`Bar`
  it doesn't know anything about the :attr:`othervalue` attribute.


.. _ipython_dir:

Configuration file location
===========================

So where should you put your configuration files? IPython uses "profiles" for
configuration, and by default, all profiles will be stored in the so called
"IPython directory". The location of this directory is determined by the
following algorithm:

* If the ``ipython-dir`` command line flag is given, its value is used.

* If not, the value returned by :func:`IPython.utils.path.get_ipython_dir`
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

Security Files
--------------

If you are using the notebook, qtconsole, or parallel code, IPython stores
connection information in small JSON files in the active profile's security
directory. This directory is made private, so only you can see the files inside. If
you need to move connection files around to other computers, this is where they will
be. If you want your code to be able to open security files by name, we have a
convenience function :func:`IPython.utils.path.get_security_file`, which will return
the absolute path to a security file from its filename and [optionally] profile
name.

.. _startup_files:

Startup Files
-------------

If you want some code to be run at the beginning of every IPython session with
a particular profile, the easiest way is to add Python (``.py``) or 
IPython (``.ipy``) scripts to your :file:`<profile>/startup` directory. Files
in this directory will always be executed as soon as the IPython shell is 
constructed, and before any other code or scripts you have specified. If you 
have multiple files in the startup directory, they will be run in 
lexicographical order, so you can control the ordering by adding a '00-' 
prefix.


.. _commandline:

Command-line arguments
======================

IPython exposes *all* configurable options on the command-line. The command-line
arguments are generated from the Configurable traits of the classes associated
with a given Application.  Configuring IPython from the command-line may look
very similar to an IPython config file

IPython applications use a parser called
:class:`~IPython.config.loader.KeyValueLoader` to load values into a Config
object.  Values are assigned in much the same way as in a config file:

.. code-block:: bash

    $ ipython --InteractiveShell.use_readline=False --BaseIPythonApplication.profile='myprofile'

Is the same as adding:

.. sourcecode:: python

    c.InteractiveShell.use_readline=False
    c.BaseIPythonApplication.profile='myprofile'

to your config file. Key/Value arguments *always* take a value, separated by '='
and no spaces.

Common Arguments
----------------

Since the strictness and verbosity of the KVLoader above are not ideal for everyday
use, common arguments can be specified as flags_ or aliases_.

Flags and Aliases are handled by :mod:`argparse` instead, allowing for more flexible
parsing. In general, flags and aliases are prefixed by ``--``, except for those
that are single characters, in which case they can be specified with a single ``-``, e.g.:

.. code-block:: bash

    $ ipython -i -c "import numpy; x=numpy.linspace(0,1)" --profile testing --colors=lightbg

Aliases
*******

For convenience, applications have a mapping of commonly used traits, so you don't have
to specify the whole class name:

.. code-block:: bash

    $ ipython --profile myprofile
    # and
    $ ipython --profile='myprofile'
    # are equivalent to
    $ ipython --BaseIPythonApplication.profile='myprofile'

Flags
*****

Applications can also be passed **flags**. Flags are options that take no
arguments. They are simply wrappers for
setting one or more configurables with predefined values, often True/False.

For instance:

.. code-block:: bash

    $ ipcontroller --debug
    # is equivalent to
    $ ipcontroller --Application.log_level=DEBUG
    # and
    $ ipython --matplotlib
    # is equivalent to
    $ ipython --matplotlib auto
    # or
    $ ipython --no-banner
    # is equivalent to
    $ ipython --TerminalIPythonApp.display_banner=False

Subcommands
-----------


Some IPython applications have **subcommands**. Subcommands are modeled after
:command:`git`, and are called with the form :command:`command subcommand
[...args]`.  Currently, the QtConsole is a subcommand of terminal IPython:

.. code-block:: bash

    $ ipython qtconsole --profile myprofile

and :command:`ipcluster` is simply a wrapper for its various subcommands (start,
stop, engines).

.. code-block:: bash

    $ ipcluster start --profile=myprofile -n 4


To see a list of the available aliases, flags, and subcommands for an IPython application, simply pass ``-h`` or ``--help``.  And to see the full list of configurable options (*very* long), pass ``--help-all``.


Design requirements
===================

Here are the main requirements we wanted our configuration system to have:

* Support for hierarchical configuration information.

* Full integration with command line option parsers.  Often, you want to read
  a configuration file, but then override some of the values with command line
  options.  Our configuration system automates this process and allows each
  command line option to be linked to a particular attribute in the 
  configuration hierarchy that it will override.

* Configuration files that are themselves valid Python code. This accomplishes
  many things. First, it becomes possible to put logic in your configuration
  files that sets attributes based on your operating system, network setup,
  Python version, etc. Second, Python has a super simple syntax for accessing
  hierarchical data structures, namely regular attribute access
  (``Foo.Bar.Bam.name``). Third, using Python makes it easy for users to
  import configuration attributes from one configuration file to another.
  Fourth, even though Python is dynamically typed, it does have types that can
  be checked at runtime. Thus, a ``1`` in a config file is the integer '1',
  while a ``'1'`` is a string.

* A fully automated method for getting the configuration information to the
  classes that need it at runtime. Writing code that walks a configuration
  hierarchy to extract a particular attribute is painful. When you have
  complex configuration information with hundreds of attributes, this makes
  you want to cry.

* Type checking and validation that doesn't require the entire configuration
  hierarchy to be specified statically before runtime. Python is a very
  dynamic language and you don't always know everything that needs to be
  configured when a program starts.

