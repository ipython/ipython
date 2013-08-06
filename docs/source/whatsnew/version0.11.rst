=============
 0.11 Series
=============

Release 0.11
============

IPython 0.11 is a *major* overhaul of IPython, two years in the making.  Most
of the code base has been rewritten or at least reorganized, breaking backward
compatibility with several APIs in previous versions.  It is the first major
release in two years, and probably the most significant change to IPython since
its inception.  We plan to have a relatively quick succession of releases, as
people discover new bugs and regressions.  Once we iron out any significant
bugs in this process and settle down the new APIs, this series will become
IPython 1.0.  We encourage feedback now on the core APIs, which we hope to
maintain stable during the 1.0 series.

Since the internal APIs have changed so much, projects using IPython as a
library (as opposed to end-users of the application) are the most likely to
encounter regressions or changes that break their existing use patterns.  We
will make every effort to provide updated versions of the APIs to facilitate
the transition, and we encourage you to contact us on the `development mailing
list`__ with questions and feedback.

.. __: http://mail.scipy.org/mailman/listinfo/ipython-dev

Chris Fonnesbeck recently wrote an `excellent post`__ that highlights some of
our major new features, with examples and screenshots.  We encourage you to
read it as it provides an illustrated, high-level overview complementing the
detailed feature breakdown in this document.

.. __: http://fonnesbeck.calepin.co/innovations-in-ipython.html

A quick summary of the major changes (see below for details):

* **Standalone Qt console**: a new rich console has been added to IPython,
  started with `ipython qtconsole`.  In this application we have tried to
  retain the feel of a terminal for fast and efficient workflows, while adding
  many features that a line-oriented terminal simply can not support, such as
  inline figures, full multiline editing with syntax highlighting, graphical
  tooltips for function calls and much more.  This development was sponsored by
  `Enthought Inc.`__. See :ref:`below <qtconsole_011>` for details.

.. __: http://enthought.com

* **High-level parallel computing with ZeroMQ**. Using the same architecture
  that our Qt console is based on, we have completely rewritten our high-level
  parallel computing machinery that in prior versions used the Twisted
  networking framework.  While this change will require users to update their
  codes, the improvements in performance, memory control and internal
  consistency across our codebase convinced us it was a price worth paying.  We
  have tried to explain how to best proceed with this update, and will be happy
  to answer questions that may arise.  A full tutorial describing these
  features `was presented at SciPy'11`__, more details :ref:`below
  <parallel_011>`.

.. __: http://minrk.github.com/scipy-tutorial-2011

* **New model for GUI/plotting support in the terminal**.  Now instead of the
  various `-Xthread` flags we had before, GUI support is provided without the
  use of any threads, by directly integrating GUI event loops with Python's
  `PyOS_InputHook` API.  A new command-line flag `--gui` controls GUI support,
  and it can also be enabled after IPython startup via the new `%gui` magic.
  This requires some changes if you want to execute GUI-using scripts inside
  IPython, see :ref:`the GUI support section <gui_support>` for more details.

* **A two-process architecture.** The Qt console is the first use of a new
  model that splits IPython between a kernel process where code is executed and
  a client that handles user interaction.  We plan on also providing terminal
  and web-browser based clients using this infrastructure in future releases.
  This model allows multiple clients to interact with an IPython process
  through a :ref:`well-documented messaging protocol <messaging>` using the
  ZeroMQ networking library.

* **Refactoring.** the entire codebase has been refactored, in order to make it
  more modular and easier to contribute to.  IPython has traditionally been a
  hard project to participate because the old codebase was very monolithic.  We
  hope this (ongoing) restructuring will make it easier for new developers to
  join us.

* **Vim integration**. Vim can be configured to seamlessly control an IPython
  kernel, see the files in :file:`docs/examples/vim` for the full details.
  This work was done by Paul Ivanov, who prepared a nice `video
  demonstration`__ of the features it provides.

.. __: http://pirsquared.org/blog/2011/07/28/vim-ipython/
  
* **Integration into Microsoft Visual Studio**. Thanks to the work of the
  Microsoft `Python Tools for Visual Studio`__ team, this version of IPython
  has been integrated into Microsoft Visual Studio's Python tools open source
  plug-in.  `Details below`_

.. __: http://pytools.codeplex.com
.. _details below: ms_visual_studio_011_

* **Improved unicode support**. We closed many bugs related to unicode input.

* **Python 3**. IPython now runs on Python 3.x. See :ref:`python3_011` for
  details.

* **New profile model**. Profiles are now directories that contain all relevant
  information for that session, and thus better isolate IPython use-cases.

* **SQLite storage for history**. All history is now stored in a SQLite
  database, providing support for multiple simultaneous sessions that won't
  clobber each other as well as the ability to perform queries on all stored
  data.

* **New configuration system**. All parts of IPython are now configured via a
  mechanism inspired by the Enthought Traits library.  Any configurable element
  can have its attributes set either via files that now use real Python syntax
  or from the command-line.

* **Pasting of code with prompts**. IPython now intelligently strips out input
  prompts , be they plain Python ones (``>>>`` and ``...``) or IPython ones
  (``In [N]:`` and ``...:``).  More details :ref:`here <pasting_with_prompts>`.
  

Authors and support
-------------------

Over 60 separate authors have contributed to this release, see :ref:`below
<credits_011>` for a full list.  In particular, we want to highlight the
extremely active participation of two new core team members: Evan Patterson
implemented the Qt console, and Thomas Kluyver started with our Python 3 port
and by now has made major contributions to just about every area of IPython.

We are also grateful for the support we have received during this development
cycle from several institutions:

- `Enthought Inc`__ funded the development of our new Qt console, an effort that
  required developing major pieces of underlying infrastructure, which now
  power not only the Qt console but also our new parallel machinery.  We'd like
  to thank Eric Jones and Travis Oliphant for their support, as well as Ilan
  Schnell for his tireless work integrating and testing IPython in the
  `Enthought Python Distribution`_.

.. __: http://enthought.com
.. _Enthought Python Distribution: http://www.enthought.com/products/epd.php

- Nipy/NIH: funding via the `NiPy project`__ (NIH grant 5R01MH081909-02) helped
  us jumpstart the development of this series by restructuring the entire
  codebase two years ago in a way that would make modular development and
  testing more approachable.  Without this initial groundwork, all the new
  features we have added would have been impossible to develop.

.. __: http://nipy.org

- Sage/NSF: funding via the grant `Sage: Unifying Mathematical Software for
  Scientists, Engineers, and Mathematicians`__ (NSF grant DMS-1015114)
  supported a meeting in spring 2011 of several of the core IPython developers
  where major progress was made integrating the last key pieces leading to this
  release.

.. __: http://modular.math.washington.edu/grants/compmath09

- Microsoft's team working on `Python Tools for Visual Studio`__ developed the 
  integraton of IPython into the Python plugin for Visual Studio 2010.

.. __: http://pytools.codeplex.com

- Google Summer of Code: in 2010, we had two students developing prototypes of
  the new machinery that is now maturing in this release: `Omar Zapata`_ and
  `Gerardo Gutiérrez`_.

.. _Omar Zapata: http://ipythonzmq.blogspot.com/2010/08/ipython-zmq-status.html
.. _Gerardo Gutiérrez: http://ipythonqt.blogspot.com/2010/04/ipython-qt-interface-gsoc-2010-proposal.html>


Development summary: moving to Git and Github
---------------------------------------------

In April 2010, after `one breakage too many with bzr`__, we decided to move our
entire development process to Git and Github.com.  This has proven to be one of
the best decisions in the project's history, as the combination of git and
github have made us far, far more productive than we could be with our previous
tools.  We first converted our bzr repo to a git one without losing history,
and a few weeks later ported all open Launchpad bugs to github issues with
their comments mostly intact (modulo some formatting changes).  This ensured a
smooth transition where no development history or submitted bugs were lost.
Feel free to use our little Launchpad to Github issues `porting script`_ if you
need to make a similar transition.

.. __: http://mail.scipy.org/pipermail/ipython-dev/2010-April/005944.html
.. _porting script: https://gist.github.com/835577

These simple statistics show how much work has been done on the new release, by
comparing the current code to the last point it had in common with the 0.10
series.  A huge diff and ~2200 commits make up this cycle::

    git diff $(git merge-base 0.10.2 HEAD)  | wc -l
    288019

    git log $(git merge-base 0.10.2 HEAD)..HEAD --oneline | wc -l
    2200

Since our move to github, 511 issues were closed, 226 of which were pull
requests and 285 regular issues (:ref:`a full list with links
<issues_list_011>` is available for those interested in the details).  Github's
pull requests are a fantastic mechanism for reviewing code and building a
shared ownership of the project, and we are making enthusiastic use of it.

.. Note::

   This undercounts the number of issues closed in this development cycle,
   since we only moved to github for issue tracking in May 2010, but we have no
   way of collecting statistics on the number of issues closed in the old
   Launchpad bug tracker prior to that.

   
.. _qtconsole_011:

Qt Console
----------

IPython now ships with a Qt application that feels very much like a terminal,
but is in fact a rich GUI that runs an IPython client but supports inline
figures, saving sessions to PDF and HTML, multiline editing with syntax
highlighting, graphical calltips and much more:

.. figure:: ../_images/qtconsole.png
    :width: 400px
    :alt: IPython Qt console with embedded plots
    :align: center
    :target: ../_images/qtconsole.png

    The Qt console for IPython, using inline matplotlib plots.

We hope that many projects will embed this widget, which we've kept
deliberately very lightweight, into their own environments.  In the future we
may also offer a slightly more featureful application (with menus and other GUI
elements), but we remain committed to always shipping this easy to embed
widget.

See the :ref:`Qt console section <qtconsole>` of the docs for a detailed
description of the console's features and use.


.. _parallel_011:

High-level parallel computing with ZeroMQ
-----------------------------------------

We have completely rewritten the Twisted-based code for high-level parallel
computing to work atop our new ZeroMQ architecture.  While we realize this will
break compatibility for a number of users, we hope to make the transition as
easy as possible with our docs, and we are convinced the change is worth it.
ZeroMQ provides us with much tighter control over memory, higher performance,
and its communications are impervious to the Python Global Interpreter Lock
because they take place in a system-level C++ thread.  The impact of the GIL in
our previous code was something we could simply not work around, given that
Twisted is itself a Python library.  So while Twisted is a very capable
framework, we think ZeroMQ fits our needs much better and we hope you will find
the change to be a significant improvement in the long run.

Our manual contains :ref:`a full description of how to use IPython for parallel
computing <parallel_overview>`, and the `tutorial`__ presented by Min
Ragan-Kelley at the SciPy 2011 conference provides a hands-on complement to the
reference docs.

.. __: http://minrk.github.com/scipy-tutorial-2011


Refactoring
-----------

As of this release, a signifiant portion of IPython has been refactored.  This
refactoring is founded on a number of new abstractions.  The main new classes
that implement these abstractions are:

* :class:`IPython.utils.traitlets.HasTraits`.
* :class:`IPython.config.configurable.Configurable`.
* :class:`IPython.config.application.Application`.
* :class:`IPython.config.loader.ConfigLoader`.
* :class:`IPython.config.loader.Config`

We are still in the process of writing developer focused documentation about
these classes, but for now our :ref:`configuration documentation
<config_overview>` contains a high level overview of the concepts that these
classes express.

The biggest user-visible change is likely the move to using the config system
to determine the command-line arguments for IPython applications. The benefit
of this is that *all* configurable values in IPython are exposed on the
command-line, but the syntax for specifying values has changed. The gist is
that assigning values is pure Python assignment.  Simple flags exist for
commonly used options, these are always prefixed with '--'.

The IPython command-line help has the details of all the options (via
``ipythyon --help``), but a simple example should clarify things; the ``pylab``
flag can be used to start in pylab mode with the qt4 backend::

  ipython --pylab=qt

which is equivalent to using the fully qualified form::

  ipython --TerminalIPythonApp.pylab=qt

The long-form options can be listed via ``ipython --help-all``.


ZeroMQ architecture
-------------------

There is a new GUI framework for IPython, based on a client-server model in
which multiple clients can communicate with one IPython kernel, using the
ZeroMQ messaging framework. There is already a Qt console client, which can
be started by calling ``ipython qtconsole``. The protocol is :ref:`documented
<messaging>`.

The parallel computing framework has also been rewritten using ZMQ. The
protocol is described :ref:`here <parallel_messages>`, and the code is in the
new :mod:`IPython.parallel` module.

.. _python3_011:

Python 3 support
----------------

A Python 3 version of IPython has been prepared. For the time being, this is
maintained separately and updated from the main codebase. Its code can be found
`here <https://github.com/ipython/ipython-py3k>`_. The parallel computing
components are not perfect on Python3, but most functionality appears to be
working.  As this work is evolving quickly, the best place to find updated
information about it is our `Python 3 wiki page`__.

.. __: http://wiki.ipython.org/index.php?title=Python_3


Unicode
-------

Entering non-ascii characters in unicode literals (``u"€ø"``) now works
properly on all platforms. However, entering these in byte/string literals
(``"€ø"``) will not work as expected on Windows (or any platform where the
terminal encoding is not UTF-8, as it typically is for Linux & Mac OS X). You
can use escape sequences (``"\xe9\x82"``) to get bytes above 128, or use
unicode literals and encode them. This is a limitation of Python 2 which we
cannot easily work around.

.. _ms_visual_studio_011:

Integration with Microsoft Visual Studio
----------------------------------------

IPython can be used as the interactive shell in the `Python plugin for
Microsoft Visual Studio`__, as seen here:

.. figure:: ../_images/ms_visual_studio.png
    :width: 500px
    :alt: IPython console embedded in Microsoft Visual Studio.
    :align: center
    :target: ../_images/ms_visual_studio.png

    IPython console embedded in Microsoft Visual Studio.

The Microsoft team developing this currently has a release candidate out using
IPython 0.11. We will continue to collaborate with them to ensure that as they
approach their final release date, the integration with IPython remains smooth.
We'd like to thank Dino Viehland and Shahrokh Mortazavi for the work they have
done towards this feature, as well as Wenming Ye for his support of our WinHPC
capabilities.

.. __: http://pytools.codeplex.com


Additional new features
-----------------------

* Added ``Bytes`` traitlet, removing ``Str``.  All 'string' traitlets should
  either be ``Unicode`` if a real string, or ``Bytes`` if a C-string. This
  removes ambiguity and helps the Python 3 transition.

* New magic ``%loadpy`` loads a python file from disk or web URL into
  the current input buffer.

* New magic ``%pastebin`` for sharing code via the 'Lodge it' pastebin.

* New magic ``%precision`` for controlling float and numpy pretty printing.

* IPython applications initiate logging, so any object can gain access to
  a the logger of the currently running Application with:

.. sourcecode:: python

    from IPython.config.application import Application
    logger = Application.instance().log

* You can now get help on an object halfway through typing a command. For
  instance, typing ``a = zip?`` shows the details of :func:`zip`. It also
  leaves the command at the next prompt so you can carry on with it.

* The input history is now written to an SQLite database. The API for
  retrieving items from the history has also been redesigned.

* The :mod:`IPython.extensions.pretty` extension has been moved out of
  quarantine and fully updated to the new extension API.

* New magics for loading/unloading/reloading extensions have been added:
  ``%load_ext``, ``%unload_ext`` and ``%reload_ext``.

* The configuration system and configuration files are brand new. See the
  configuration system :ref:`documentation <config_index>` for more details.

* The :class:`~IPython.core.interactiveshell.InteractiveShell` class is now a
  :class:`~IPython.config.configurable.Configurable` subclass and has traitlets
  that determine the defaults and runtime environment. The ``__init__`` method
  has also been refactored so this class can be instantiated and run without
  the old :mod:`ipmaker` module.

* The methods of :class:`~IPython.core.interactiveshell.InteractiveShell` have
  been organized into sections to make it easier to turn more sections
  of functionality into components.

* The embedded shell has been refactored into a truly standalone subclass of
  :class:`InteractiveShell` called :class:`InteractiveShellEmbed`.  All
  embedding logic has been taken out of the base class and put into the 
  embedded subclass.

* Added methods of :class:`~IPython.core.interactiveshell.InteractiveShell` to
  help it cleanup after itself. The :meth:`cleanup` method controls this. We
  couldn't do this in :meth:`__del__` because we have cycles in our object
  graph that prevent it from being called.

* Created a new module :mod:`IPython.utils.importstring` for resolving
  strings like ``foo.bar.Bar`` to the actual class.

* Completely refactored the :mod:`IPython.core.prefilter` module into
  :class:`~IPython.config.configurable.Configurable` subclasses. Added a new
  layer into the prefilter system, called "transformations" that all new
  prefilter logic should use (rather than the older "checker/handler"
  approach).

* Aliases are now components (:mod:`IPython.core.alias`).

* New top level :func:`~IPython.frontend.terminal.embed.embed` function that can
  be called to embed IPython at any place in user's code. On the first call it
  will create an :class:`~IPython.frontend.terminal.embed.InteractiveShellEmbed`
  instance and call it. In later calls, it just calls the previously created
  :class:`~IPython.frontend.terminal.embed.InteractiveShellEmbed`.

* Created a configuration system (:mod:`IPython.config.configurable`) that is
  based on :mod:`IPython.utils.traitlets`. Configurables are arranged into a
  runtime containment tree (not inheritance) that i) automatically propagates
  configuration information and ii) allows singletons to discover each other in
  a loosely coupled manner. In the future all parts of IPython will be
  subclasses of :class:`~IPython.config.configurable.Configurable`. All IPython
  developers should become familiar with the config system.

* Created a new :class:`~IPython.config.loader.Config` for holding
  configuration information. This is a dict like class with a few extras: i)
  it supports attribute style access, ii) it has a merge function that merges
  two :class:`~IPython.config.loader.Config` instances recursively and iii) it
  will automatically create sub-:class:`~IPython.config.loader.Config`
  instances for attributes that start with an uppercase character.

* Created new configuration loaders in :mod:`IPython.config.loader`. These
  loaders provide a unified loading interface for all configuration
  information including command line arguments and configuration files. We
  have two default implementations based on :mod:`argparse` and plain python
  files.  These are used to implement the new configuration system.

* Created a top-level :class:`Application` class in
  :mod:`IPython.core.application` that is designed to encapsulate the starting
  of any basic Python program. An application loads and merges all the
  configuration objects, constructs the main application, configures and
  initiates logging, and creates and configures any :class:`Configurable`
  instances and then starts the application running. An extended
  :class:`BaseIPythonApplication` class adds logic for handling the
  IPython directory as well as profiles, and all IPython entry points
  extend it.

* The :class:`Type` and :class:`Instance` traitlets now handle classes given
  as strings, like ``foo.bar.Bar``. This is needed for forward declarations.
  But, this was implemented in a careful way so that string to class
  resolution is done at a single point, when the parent
  :class:`~IPython.utils.traitlets.HasTraitlets` is instantiated.

* :mod:`IPython.utils.ipstruct` has been refactored to be a subclass of 
  dict.  It also now has full docstrings and doctests.

* Created a Traits like implementation in :mod:`IPython.utils.traitlets`.  This
  is a pure Python, lightweight version of a library that is similar to
  Enthought's Traits project, but has no dependencies on Enthought's code.  We
  are using this for validation, defaults and notification in our new component
  system.  Although it is not 100% API compatible with Enthought's Traits, we
  plan on moving in this direction so that eventually our implementation could
  be replaced by a (yet to exist) pure Python version of Enthought Traits.

* Added a new module :mod:`IPython.lib.inputhook` to manage the integration
  with GUI event loops using `PyOS_InputHook`.  See the docstrings in this
  module or the main IPython docs for details.

* For users, GUI event loop integration is now handled through the new
  :command:`%gui` magic command.  Type ``%gui?`` at an IPython prompt for
  documentation.

* For developers :mod:`IPython.lib.inputhook` provides a simple interface
  for managing the event loops in their interactive GUI applications.
  Examples can be found in our :file:`examples/lib` directory.

Backwards incompatible changes
------------------------------

* The Twisted-based :mod:`IPython.kernel` has been removed, and completely
  rewritten as :mod:`IPython.parallel`, using ZeroMQ.

* Profiles are now directories. Instead of a profile being a single config file,
  profiles are now self-contained directories. By default, profiles get their
  own IPython history, log files, and everything. To create a new profile, do
  ``ipython profile create <name>``.

* All IPython applications have been rewritten to use
  :class:`~IPython.config.loader.KeyValueConfigLoader`. This means that
  command-line options have changed. Now, all configurable values are accessible
  from the command-line with the same syntax as in a configuration file.

* The command line options ``-wthread``, ``-qthread`` and
  ``-gthread`` have been removed. Use ``--gui=wx``, ``--gui=qt``, ``--gui=gtk``
  instead.

* The extension loading functions have been renamed to
  :func:`load_ipython_extension` and :func:`unload_ipython_extension`.

* :class:`~IPython.core.interactiveshell.InteractiveShell` no longer takes an
  ``embedded`` argument. Instead just use the
  :class:`~IPython.core.interactiveshell.InteractiveShellEmbed` class.

* ``__IPYTHON__`` is no longer injected into ``__builtin__``.

* :meth:`Struct.__init__` no longer takes `None` as its first argument.  It
  must be a :class:`dict` or :class:`Struct`.

* :meth:`~IPython.core.interactiveshell.InteractiveShell.ipmagic` has been
  renamed :meth:`~IPython.core.interactiveshell.InteractiveShell.magic.`

* The functions :func:`ipmagic` and :func:`ipalias` have been removed from
  :mod:`__builtins__`.

* The references to the global
  :class:`~IPython.core.interactivehell.InteractiveShell` instance (``_ip``, and
  ``__IP``) have been removed from the user's namespace. They are replaced by a
  new function called :func:`get_ipython` that returns the current
  :class:`~IPython.core.interactiveshell.InteractiveShell` instance. This
  function is injected into the user's namespace and is now the main way of
  accessing the running IPython.

* Old style configuration files :file:`ipythonrc` and :file:`ipy_user_conf.py`
  are no longer supported. Users should migrate there configuration files to
  the new format described :ref:`here <config_overview>` and :ref:`here
  <configuring_ipython>`.

* The old IPython extension API that relied on :func:`ipapi` has been
  completely removed. The new extension API is described :ref:`here
  <configuring_ipython>`.

* Support for ``qt3`` has been dropped.  Users who need this should use
  previous versions of IPython.

* Removed :mod:`shellglobals` as it was obsolete.

* Removed all the threaded shells in :mod:`IPython.core.shell`. These are no
  longer needed because of the new capabilities in
  :mod:`IPython.lib.inputhook`.

* New top-level sub-packages have been created: :mod:`IPython.core`, 
  :mod:`IPython.lib`, :mod:`IPython.utils`, :mod:`IPython.deathrow`,
  :mod:`IPython.quarantine`.  All existing top-level modules have been
  moved to appropriate sub-packages.  All internal import statements
  have been updated and tests have been added.  The build system (setup.py
  and friends) have been updated.  See :ref:`this section <module_reorg>` of the
  documentation for descriptions of these new sub-packages.

* :mod:`IPython.ipapi` has been moved to :mod:`IPython.core.ipapi`.
  :mod:`IPython.Shell` and :mod:`IPython.iplib` have been split and removed as
  part of the refactor.

* :mod:`Extensions` has been moved to :mod:`extensions` and all existing
  extensions have been moved to either :mod:`IPython.quarantine` or
  :mod:`IPython.deathrow`. :mod:`IPython.quarantine` contains modules that we
  plan on keeping but that need to be updated. :mod:`IPython.deathrow` contains
  modules that are either dead or that should be maintained as third party
  libraries. More details about this can be found :ref:`here <module_reorg>`.

* Previous IPython GUIs in :mod:`IPython.frontend` and :mod:`IPython.gui` are
  likely broken, and have been removed to :mod:`IPython.deathrow` because of the
  refactoring in the core. With proper updates, these should still work.


Known Regressions
-----------------

We do our best to improve IPython, but there are some known regressions in 0.11
relative to 0.10.2.  First of all, there are features that have yet to be
ported to the new APIs, and in order to ensure that all of the installed code
runs for our users, we have moved them to two separate directories in the
source distribution, `quarantine` and `deathrow`.  Finally, we have some other
miscellaneous regressions that we hope to fix as soon as possible.  We now
describe all of these in more detail.

Quarantine
~~~~~~~~~~

These are tools and extensions that we consider relatively easy to update to
the new classes and APIs, but that we simply haven't had time for.  Any user
who is interested in one of these is encouraged to help us by porting it and
submitting a pull request on our `development site`_.

.. _development site: http://github.com/ipython/ipython

Currently, the quarantine directory contains::

    clearcmd.py            ipy_fsops.py            ipy_signals.py
    envpersist.py          ipy_gnuglobal.py        ipy_synchronize_with.py
    ext_rescapture.py      ipy_greedycompleter.py  ipy_system_conf.py
    InterpreterExec.py     ipy_jot.py              ipy_which.py
    ipy_app_completers.py  ipy_lookfor.py          ipy_winpdb.py
    ipy_autoreload.py      ipy_profile_doctest.py  ipy_workdir.py
    ipy_completers.py      ipy_pydb.py             jobctrl.py
    ipy_editors.py         ipy_rehashdir.py        ledit.py
    ipy_exportdb.py        ipy_render.py           pspersistence.py
    ipy_extutil.py         ipy_server.py           win32clip.py

Deathrow
~~~~~~~~

These packages may be harder to update or make most sense as third-party
libraries.  Some of them are completely obsolete and have been already replaced
by better functionality (we simply haven't had the time to carefully weed them
out so they are kept here for now). Others simply require fixes to code that
the current core team may not be familiar with.  If a tool you were used to is
included here, we encourage you to contact the dev list and we can discuss
whether it makes sense to keep it in IPython (if it can be maintained).

Currently, the deathrow directory contains::

    astyle.py              ipy_defaults.py          ipy_vimserver.py
    dtutils.py             ipy_kitcfg.py            numeric_formats.py
    Gnuplot2.py            ipy_legacy.py            numutils.py
    GnuplotInteractive.py  ipy_p4.py                outputtrap.py
    GnuplotRuntime.py      ipy_profile_none.py      PhysicalQInput.py
    ibrowse.py             ipy_profile_numpy.py     PhysicalQInteractive.py
    igrid.py               ipy_profile_scipy.py     quitter.py*
    ipipe.py               ipy_profile_sh.py        scitedirector.py
    iplib.py               ipy_profile_zope.py      Shell.py
    ipy_constants.py       ipy_traits_completer.py  twshell.py


Other regressions
~~~~~~~~~~~~~~~~~

* The machinery that adds functionality to the 'sh' profile for using IPython
  as your system shell has not been updated to use the new APIs.  As a result,
  only the aesthetic (prompt) changes are still implemented. We intend to fix
  this by 0.12.  Tracked as issue 547_.

.. _547: https://github.com/ipython/ipython/issues/547

* The installation of scripts on Windows was broken without setuptools, so we
  now depend on setuptools on Windows.  We hope to fix setuptools-less
  installation, and then remove the setuptools dependency.  Issue 539_.

.. _539: https://github.com/ipython/ipython/issues/539

* The directory history `_dh` is not saved between sessions.  Issue 634_.

.. _634: https://github.com/ipython/ipython/issues/634


Removed Features
----------------

As part of the updating of IPython, we have removed a few features for the
purposes of cleaning up the codebase and interfaces.  These removals are
permanent, but for any item listed below, equivalent functionality is
available.

* The magics Exit and Quit have been dropped as ways to exit IPython. Instead,
  the lowercase forms of both work either as a bare name (``exit``) or a
  function call (``exit()``).  You can assign these to other names using
  exec_lines in the config file.


.. _credits_011:

Credits
-------

Many users and developers contributed code, features, bug reports and ideas to
this release.  Please do not hesitate in contacting us if we've failed to
acknowledge your contribution here.  In particular, for this release we have
contribution from the following people, a mix of new and regular names (in
alphabetical order by first name):

* Aenugu Sai Kiran Reddy <saikrn08-at-gmail.com>
* andy wilson <wilson.andrew.j+github-at-gmail.com>
* Antonio Cuni <antocuni>
* Barry Wark <barrywark-at-gmail.com>
* Beetoju Anuradha <anu.beethoju-at-gmail.com>
* Benjamin Ragan-Kelley <minrk-at-Mercury.local>
* Brad Reisfeld
* Brian E. Granger <ellisonbg-at-gmail.com>
* Christoph Gohlke <cgohlke-at-uci.edu>
* Cody Precord
* dan.milstein
* Darren Dale <dsdale24-at-gmail.com>
* Dav Clark <davclark-at-berkeley.edu>
* David Warde-Farley <wardefar-at-iro.umontreal.ca>
* epatters <ejpatters-at-gmail.com>
* epatters <epatters-at-caltech.edu>
* epatters <epatters-at-enthought.com>
* Eric Firing <efiring-at-hawaii.edu>
* Erik Tollerud <erik.tollerud-at-gmail.com>
* Evan Patterson <epatters-at-enthought.com>
* Fernando Perez <Fernando.Perez-at-berkeley.edu>
* Gael Varoquaux <gael.varoquaux-at-normalesup.org>
* Gerardo <muzgash-at-Muzpelheim>
* Jason Grout <jason.grout-at-drake.edu>
* John Hunter <jdh2358-at-gmail.com>
* Jens Hedegaard Nielsen <jenshnielsen-at-gmail.com>
* Johann Cohen-Tanugi <johann.cohentanugi-at-gmail.com>
* Jörgen Stenarson <jorgen.stenarson-at-bostream.nu>
* Justin Riley <justin.t.riley-at-gmail.com>
* Kiorky
* Laurent Dufrechou <laurent.dufrechou-at-gmail.com>
* Luis Pedro Coelho <lpc-at-cmu.edu>
* Mani chandra <mchandra-at-iitk.ac.in>
* Mark E. Smith
* Mark Voorhies <mark.voorhies-at-ucsf.edu>
* Martin Spacek <git-at-mspacek.mm.st>
* Michael Droettboom <mdroe-at-stsci.edu>
* MinRK <benjaminrk-at-gmail.com>
* muzuiget <muzuiget-at-gmail.com>
* Nick Tarleton <nick-at-quixey.com>
* Nicolas Rougier <Nicolas.rougier-at-inria.fr>
* Omar Andres Zapata Mesa <andresete.chaos-at-gmail.com>
* Paul Ivanov <pivanov314-at-gmail.com>
* Pauli Virtanen <pauli.virtanen-at-iki.fi>
* Prabhu Ramachandran
* Ramana <sramana9-at-gmail.com>
* Robert Kern <robert.kern-at-gmail.com>
* Sathesh Chandra <satheshchandra88-at-gmail.com>
* Satrajit Ghosh <satra-at-mit.edu>
* Sebastian Busch
* Skipper Seabold <jsseabold-at-gmail.com>
* Stefan van der Walt <bzr-at-mentat.za.net>
* Stephan Peijnik <debian-at-sp.or.at>
* Steven Bethard
* Thomas Kluyver <takowl-at-gmail.com>
* Thomas Spura <tomspur-at-fedoraproject.org>
* Tom Fetherston <tfetherston-at-aol.com>
* Tom MacWright
* tzanko
* vankayala sowjanya <hai.sowjanya-at-gmail.com>
* Vivian De Smedt <vds2212-at-VIVIAN>
* Ville M. Vainio <vivainio-at-gmail.com>
* Vishal Vatsa <vishal.vatsa-at-gmail.com>
* Vishnu S G <sgvishnu777-at-gmail.com>
* Walter Doerwald <walter-at-livinglogic.de>

.. note::

    This list was generated with the output of
    ``git log dev-0.11 HEAD --format='* %aN <%aE>' | sed 's/@/\-at\-/' | sed 's/<>//' | sort -u``
    after some cleanup.  If you should be on this list, please add yourself.
