========================================
0.9 series
========================================

Release 0.9.1
=============

This release was quickly made to restore compatibility with Python 2.4, which
version 0.9 accidentally broke.  No new features were introduced, other than
some additional testing support for internal use.


Release 0.9
===========

New features
------------

* All furl files and security certificates are now put in a read-only
  directory named ~/.ipython/security.

* A single function :func:`get_ipython_dir`, in :mod:`IPython.genutils` that
  determines the user's IPython directory in a robust manner.

* Laurent's WX application has been given a top-level script called
  ipython-wx, and it has received numerous fixes. We expect this code to be
  architecturally better integrated with Gael's WX 'ipython widget' over the
  next few releases.

* The Editor synchronization work by Vivian De Smedt has been merged in.  This
  code adds a number of new editor hooks to synchronize with editors under
  Windows.

* A new, still experimental but highly functional, WX shell by Gael Varoquaux.
  This work was sponsored by Enthought, and while it's still very new, it is
  based on a more cleanly organized arhictecture of the various IPython
  components. We will continue to develop this over the next few releases as a
  model for GUI components that use IPython.

* Another GUI frontend, Cocoa based (Cocoa is the OSX native GUI framework),
  authored by Barry Wark.  Currently the WX and the Cocoa ones have slightly
  different internal organizations, but the whole team is working on finding
  what the right abstraction points are for a unified codebase.

* As part of the frontend work, Barry Wark also implemented an experimental
  event notification system that various ipython components can use.  In the
  next release the implications and use patterns of this system regarding the
  various GUI options will be worked out.

* IPython finally has a full test system, that can test docstrings with
  IPython-specific functionality.  There are still a few pieces missing for it
  to be widely accessible to all users (so they can run the test suite at any
  time and report problems), but it now works for the developers.  We are
  working hard on continuing to improve it, as this was probably IPython's
  major Achilles heel (the lack of proper test coverage made it effectively
  impossible to do large-scale refactoring).  The full test suite can now
  be run using the :command:`iptest` command line program.

* The notion of a task has been completely reworked.  An `ITask` interface has
  been created.  This interface defines the methods that tasks need to
  implement.  These methods are now responsible for things like submitting
  tasks and processing results.  There are two basic task types:
  :class:`IPython.kernel.task.StringTask` (this is the old `Task` object, but
  renamed) and the new :class:`IPython.kernel.task.MapTask`, which is based on
  a function.

* A new interface, :class:`IPython.kernel.mapper.IMapper` has been defined to
  standardize the idea of a `map` method.  This interface has a single `map`
  method that has the same syntax as the built-in `map`.  We have also defined
  a `mapper` factory interface that creates objects that implement
  :class:`IPython.kernel.mapper.IMapper` for different controllers.  Both the
  multiengine and task controller now have mapping capabilties.

* The parallel function capabilities have been reworks.  The major changes are
  that i) there is now an `@parallel` magic that creates parallel functions,
  ii) the syntax for multiple variable follows that of `map`, iii) both the
  multiengine and task controller now have a parallel function implementation.

* All of the parallel computing capabilities from `ipython1-dev` have been
  merged into IPython proper.  This resulted in the following new subpackages:
  :mod:`IPython.kernel`, :mod:`IPython.kernel.core`, :mod:`IPython.config`,
  :mod:`IPython.tools` and :mod:`IPython.testing`.

* As part of merging in the `ipython1-dev` stuff, the `setup.py` script and
  friends have been completely refactored.  Now we are checking for
  dependencies using the approach that matplotlib uses.

* The documentation has been completely reorganized to accept the 
  documentation from `ipython1-dev`.

* We have switched to using Foolscap for all of our network protocols in
  :mod:`IPython.kernel`.  This gives us secure connections that are both
  encrypted and authenticated.

* We have a brand new `COPYING.txt` files that describes the IPython license
  and copyright. The biggest change is that we are putting "The IPython
  Development Team" as the copyright holder. We give more details about
  exactly what this means in this file. All developer should read this and use
  the new banner in all IPython source code files.

* sh profile: ./foo runs foo as system command, no need to do !./foo anymore

* String lists now support ``sort(field, nums = True)`` method (to easily sort
  system command output). Try it with ``a = !ls -l ; a.sort(1, nums=1)``.

* '%cpaste foo' now assigns the pasted block as string list, instead of string

* The ipcluster script now run by default with no security.  This is done
  because the main usage of the script is for starting things on localhost.
  Eventually when ipcluster is able to start things on other hosts, we will put
  security back.

* 'cd --foo' searches directory history for string foo, and jumps to that dir.
  Last part of dir name is checked first. If no matches for that are found,
  look at the whole path.

  
Bug fixes
---------

* The Windows installer has been fixed.  Now all IPython scripts have ``.bat``
  versions created.  Also, the Start Menu shortcuts have been updated.

* The colors escapes in the multiengine client are now turned off on win32 as
  they don't print correctly.

* The :mod:`IPython.kernel.scripts.ipengine` script was exec'ing
  mpi_import_statement incorrectly, which was leading the engine to crash when
  mpi was enabled.

* A few subpackages had missing ``__init__.py`` files.

* The documentation is only created if Sphinx is found.  Previously, the
  ``setup.py`` script would fail if it was missing.

* Greedy ``cd`` completion has been disabled again (it was enabled in 0.8.4) as
  it caused problems on certain platforms.
          

Backwards incompatible changes
------------------------------

* The ``clusterfile`` options of the :command:`ipcluster` command has been
  removed as it was not working and it will be replaced soon by something much
  more robust.

* The :mod:`IPython.kernel` configuration now properly find the user's
  IPython directory.

* In ipapi, the :func:`make_user_ns` function has been replaced with
  :func:`make_user_namespaces`, to support dict subclasses in namespace
  creation.

* :class:`IPython.kernel.client.Task` has been renamed
  :class:`IPython.kernel.client.StringTask` to make way for new task types.

* The keyword argument `style` has been renamed `dist` in `scatter`, `gather`
  and `map`.

* Renamed the values that the rename `dist` keyword argument can have from
  `'basic'` to `'b'`.

* IPython has a larger set of dependencies if you want all of its capabilities.
  See the `setup.py` script for details.

* The constructors for :class:`IPython.kernel.client.MultiEngineClient` and 
  :class:`IPython.kernel.client.TaskClient` no longer take the (ip,port) tuple.
  Instead they take the filename of a file that contains the FURL for that
  client.  If the FURL file is in your IPYTHONDIR, it will be found automatically
  and the constructor can be left empty.

* The asynchronous clients in :mod:`IPython.kernel.asyncclient` are now created 
  using the factory functions :func:`get_multiengine_client` and 
  :func:`get_task_client`.  These return a `Deferred` to the actual client.

* The command line options to `ipcontroller` and `ipengine` have changed to
  reflect the new Foolscap network protocol and the FURL files.  Please see the
  help for these scripts for details.

* The configuration files for the kernel have changed because of the Foolscap
  stuff.  If you were using custom config files before, you should delete them
  and regenerate new ones.

Changes merged in from IPython1
-------------------------------

New features
............

* Much improved ``setup.py`` and ``setupegg.py`` scripts.  Because Twisted and
  zope.interface are now easy installable, we can declare them as dependencies
  in our setupegg.py script.

* IPython is now compatible with Twisted 2.5.0 and 8.x.

* Added a new example of how to use :mod:`ipython1.kernel.asynclient`.

* Initial draft of a process daemon in :mod:`ipython1.daemon`.  This has not
  been merged into IPython and is still in `ipython1-dev`.
  
* The ``TaskController`` now has methods for getting the queue status.

* The ``TaskResult`` objects not have information about how long the task
  took to run.
  
* We are attaching additional attributes to exceptions ``(_ipython_*)`` that 
  we use to carry additional info around.
  
* New top-level module :mod:`asyncclient` that has asynchronous versions (that
  return deferreds) of the client classes.  This is designed to users who want
  to run their own Twisted reactor.
  
* All the clients in :mod:`client` are now based on Twisted.  This is done by 
  running the Twisted reactor in a separate thread and using the
  :func:`blockingCallFromThread` function that is in recent versions of Twisted.

* Functions can now be pushed/pulled to/from engines using
  :meth:`MultiEngineClient.push_function` and
  :meth:`MultiEngineClient.pull_function`.

* Gather/scatter are now implemented in the client to reduce the work load
  of the controller and improve performance.

* Complete rewrite of the IPython docuementation.  All of the documentation
  from the IPython website has been moved into docs/source as restructured
  text documents.  PDF and HTML documentation are being generated using 
  Sphinx.

* New developer oriented documentation: development guidelines and roadmap. 

* Traditional ``ChangeLog`` has been changed to a more useful ``changes.txt``
  file that is organized by release and is meant to provide something more
  relevant for users.

Bug fixes
.........

* Created a proper ``MANIFEST.in`` file to create source distributions.

* Fixed a bug in the ``MultiEngine`` interface.  Previously, multi-engine 
  actions were being collected with a :class:`DeferredList` with 
  ``fireononeerrback=1``.  This meant that methods were returning 
  before all engines had given their results.  This was causing extremely odd 
  bugs in certain cases. To fix this problem, we have 1) set 
  ``fireononeerrback=0`` to make sure all results (or exceptions) are in 
  before returning and 2) introduced a :exc:`CompositeError` exception 
  that wraps all of the engine exceptions.  This is a huge change as it means 
  that users will have to catch :exc:`CompositeError` rather than the actual
  exception.

Backwards incompatible changes
..............................

* All names have been renamed to conform to the lowercase_with_underscore
  convention.  This will require users to change references to all names like
  ``queueStatus`` to ``queue_status``.

* Previously, methods like :meth:`MultiEngineClient.push` and
  :meth:`MultiEngineClient.push` used ``*args`` and ``**kwargs``.  This was
  becoming a problem as we weren't able to introduce new keyword arguments into
  the API.  Now these methods simple take a dict or sequence.  This has also
  allowed us to get rid of the ``*All`` methods like :meth:`pushAll` and
  :meth:`pullAll`.  These things are now handled with the ``targets`` keyword
  argument that defaults to ``'all'``.

* The :attr:`MultiEngineClient.magicTargets` has been renamed to
  :attr:`MultiEngineClient.targets`. 

* All methods in the MultiEngine interface now accept the optional keyword
  argument ``block``.

* Renamed :class:`RemoteController` to :class:`MultiEngineClient` and 
  :class:`TaskController` to :class:`TaskClient`.

* Renamed the top-level module from :mod:`api` to :mod:`client`.

* Most methods in the multiengine interface now raise a :exc:`CompositeError`
  exception that wraps the user's exceptions, rather than just raising the raw
  user's exception.

* Changed the ``setupNS`` and ``resultNames`` in the ``Task`` class to ``push`` 
  and ``pull``.

