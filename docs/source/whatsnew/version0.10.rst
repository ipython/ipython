=============
 0.10 series
=============

Release 0.10.2
==============

IPython 0.10.2 was released April 9, 2011.  This is a minor bugfix release that
preserves backward compatibility.  At this point, all IPython development
resources are focused on the 0.11 series that includes a complete architectural
restructuring of the project as well as many new capabilities, so this is
likely to be the last release of the 0.10.x series.  We have tried to fix all
major bugs in this series so that it remains a viable platform for those not
ready yet to transition to the 0.11 and newer codebase (since that will require
some porting effort, as a number of APIs have changed).

Thus, we are not opening a 0.10.3 active development branch yet, but if the
user community requires new patches and is willing to maintain/release such a
branch, we'll be happy to host it on the IPython github repositories.

Highlights of this release:

- The main one is the closing of github ticket #185, a major regression we had
  in 0.10.1 where pylab mode with GTK (or gthread) was not working correctly,
  hence plots were blocking with GTK.  Since this is the default matplotlib
  backend on Unix systems, this was a major annoyance for many users.  Many
  thanks to Paul Ivanov for helping resolve this issue.
  
- Fix IOError bug on Windows when used with -gthread.
- Work robustly if $HOME is missing from environment.
- Better POSIX support in ssh scripts (remove bash-specific idioms).
- Improved support for non-ascii characters in log files.
- Work correctly in environments where GTK can be imported but not started
  (such as a linux text console without X11).
  
For this release we merged 24 commits, contributed by the following people
(please let us know if we ommitted your name and we'll gladly fix this in the
notes for the future):

* Fernando Perez
* MinRK
* Paul Ivanov
* Pieter Cristiaan de Groot
* TvrtkoM

Release 0.10.1
==============

IPython 0.10.1 was released October 11, 2010, over a year after version 0.10.
This is mostly a bugfix release, since after version 0.10 was released, the
development team's energy has been focused on the 0.11 series.  We have
nonetheless tried to backport what fixes we could into 0.10.1, as it remains
the stable series that many users have in production systems they rely on.

Since the 0.11 series changes many APIs in backwards-incompatible ways, we are
willing to continue maintaining the 0.10.x series.  We don't really have time
to actively write new code for 0.10.x, but we are happy to accept patches and
pull requests on the IPython `github site`_.  If sufficient contributions are
made that improve 0.10.1, we will roll them into future releases.  For this
purpose, we will have a branch called 0.10.2 on github, on which you can base
your contributions.

.. _github site: http://github.com/ipython

For this release, we applied approximately 60 commits totaling a diff of over
7000 lines::

    (0.10.1)amirbar[dist]> git diff --oneline rel-0.10.. | wc -l
    7296

Highlights of this release:

- The only significant new feature is that IPython's parallel computing
  machinery now supports natively the Sun Grid Engine and LSF schedulers.  This
  work was a joint contribution from Justin Riley, Satra Ghosh and Matthieu
  Brucher, who put a lot of work into it.  We also improved traceback handling
  in remote tasks, as well as providing better control for remote task IDs.

- New IPython Sphinx directive contributed by John Hunter.  You can use this
  directive to mark blocks in reSructuredText documents as containing IPython
  syntax (including figures) and the will be executed during the build:

  .. sourcecode:: ipython

      In [2]: plt.figure()  # ensure a fresh figure

      @savefig psimple.png width=4in
      In [3]: plt.plot([1,2,3])
      Out[3]: [<matplotlib.lines.Line2D object at 0x9b74d8c>]

- Various fixes to the standalone ipython-wx application.

- We now ship internally the excellent argparse library, graciously licensed
  under BSD terms by Steven Bethard.  Now (2010) that argparse has become part
  of Python 2.7 this will be less of an issue, but Steven's relicensing allowed
  us to start updating IPython to using argparse well before Python 2.7.  Many
  thanks!

- Robustness improvements so that IPython doesn't crash if the readline library
  is absent (though obviously a lot of functionality that requires readline
  will not be available).

- Improvements to tab completion in Emacs with Python 2.6.

- Logging now supports timestamps (see ``%logstart?`` for full details).

- A long-standing and quite annoying bug where parentheses would be added to
  ``print`` statements, under Python 2.5 and 2.6, was finally fixed.

- Improved handling of libreadline on Apple OSX.

- Fix ``reload`` method of IPython demos, which was broken.

- Fixes for the ipipe/ibrowse system on OSX.

- Fixes for Zope profile.

- Fix %timeit reporting when the time is longer than 1000s.

- Avoid lockups with ? or ?? in SunOS, due to a bug in termios.

- The usual assortment of miscellaneous bug fixes and small improvements.

The following people contributed to this release (please let us know if we
omitted your name and we'll gladly fix this in the notes for the future):

* Beni Cherniavsky
* Boyd Waters.
* David Warde-Farley
* Fernando Perez
* Gökhan Sever
* John Hunter
* Justin Riley
* Kiorky
* Laurent Dufrechou
* Mark E. Smith
* Matthieu Brucher
* Satrajit Ghosh
* Sebastian Busch
* Václav Šmilauer

Release 0.10
============

This release brings months of slow but steady development, and will be the last
before a major restructuring and cleanup of IPython's internals that is already
under way.  For this reason, we hope that 0.10 will be a stable and robust
release so that while users adapt to some of the API changes that will come
with the refactoring that will become IPython 0.11, they can safely use 0.10 in
all existing projects with minimal changes (if any).

IPython 0.10 is now a medium-sized project, with roughly (as reported by David
Wheeler's :command:`sloccount` utility) 40750 lines of Python code, and a diff
between 0.9.1 and this release that contains almost 28000 lines of code and
documentation.  Our documentation, in PDF format, is a 495-page long PDF
document (also available in HTML format, both generated from the same sources).

Many users and developers contributed code, features, bug reports and ideas to
this release.  Please do not hesitate in contacting us if we've failed to
acknowledge your contribution here.  In particular, for this release we have
contribution from the following people, a mix of new and regular names (in
alphabetical order by first name):

* Alexander Clausen: fix #341726.
* Brian Granger: lots of work everywhere (features, bug fixes, etc).
* Daniel Ashbrook: bug report on MemoryError during compilation, now fixed.
* Darren Dale: improvements to documentation build system, feedback, design
  ideas.
* Fernando Perez: various places.
* Gaël Varoquaux: core code, ipythonx GUI, design discussions, etc. Lots...
* John Hunter: suggestions, bug fixes, feedback.
* Jorgen Stenarson: work on many fronts, tests, fixes, win32 support, etc.
* Laurent Dufréchou: many improvements to ipython-wx standalone app.
* Lukasz Pankowski: prefilter, `%edit`, demo improvements.
* Matt Foster: TextMate support in `%edit`.
* Nathaniel Smith: fix #237073.
* Pauli Virtanen: fixes and improvements to extensions, documentation.
* Prabhu Ramachandran: improvements to `%timeit`.
* Robert Kern: several extensions.
* Sameer D'Costa: help on critical bug #269966.
* Stephan Peijnik: feedback on Debian compliance and many man pages.
* Steven Bethard: we are now shipping his :mod:`argparse` module.
* Tom Fetherston: many improvements to :mod:`IPython.demo` module.
* Ville Vainio: lots of work everywhere (features, bug fixes, etc).
* Vishal Vasta: ssh support in ipcluster.
* Walter Doerwald: work on the :mod:`IPython.ipipe` system.

Below we give an overview of new features, bug fixes and backwards-incompatible
changes.  For a detailed account of every change made, feel free to view the
project log with :command:`bzr log`.

New features
------------

* New `%paste` magic automatically extracts current contents of clipboard and
  pastes it directly, while correctly handling code that is indented or
  prepended with `>>>` or `...` python prompt markers.  A very useful new
  feature contributed by Robert Kern.

* IPython 'demos', created with the :mod:`IPython.demo` module, can now be
  created from files on disk or strings in memory.  Other fixes and
  improvements to the demo system, by Tom Fetherston.

* Added :func:`find_cmd` function to :mod:`IPython.platutils` module, to find
  commands in a cross-platform manner.

* Many improvements and fixes to Gaël Varoquaux's :command:`ipythonx`, a
  WX-based lightweight IPython instance that can be easily embedded in other WX
  applications.  These improvements have made it possible to now have an
  embedded IPython in Mayavi and other tools.

* :class:`MultiengineClient` objects now have a :meth:`benchmark` method.

* The manual now includes a full set of auto-generated API documents from the
  code sources, using Sphinx and some of our own support code.  We are now
  using the `Numpy Documentation Standard`_  for all docstrings, and we have
  tried to update as many existing ones as possible to this format.

* The new :mod:`IPython.Extensions.ipy_pretty` extension by Robert Kern
  provides configurable pretty-printing.

* Many improvements to the :command:`ipython-wx` standalone WX-based IPython
  application by Laurent Dufréchou.  It can optionally run in a thread, and
  this can be toggled at runtime (allowing the loading of Matplotlib in a
  running session without ill effects).

* IPython includes a copy of Steven Bethard's argparse_ in the
  :mod:`IPython.external` package, so we can use it internally and it is also
  available to any IPython user.  By installing it in this manner, we ensure
  zero conflicts with any system-wide installation you may already have while
  minimizing external dependencies for new users.  In IPython 0.10, We ship
  argparse version 1.0.

* An improved and much more robust test suite, that runs groups of tests in
  separate subprocesses using either Nose or Twisted's :command:`trial` runner
  to ensure proper management of Twisted-using code.  The test suite degrades
  gracefully if optional dependencies are not available, so that the
  :command:`iptest` command can be run with only Nose installed and nothing
  else.  We also have more and cleaner test decorators to better select tests
  depending on runtime conditions, do setup/teardown, etc.

* The new ipcluster now has a fully working ssh mode that should work on
  Linux, Unix and OS X.  Thanks to Vishal Vatsa for implementing this!

* The wonderful TextMate editor can now be used with %edit on OS X.  Thanks
  to Matt Foster for this patch.

* The documentation regarding parallel uses of IPython, including MPI and PBS,
  has been significantly updated and improved.

* The developer guidelines in the documentation have been updated to explain
  our workflow using :command:`bzr` and Launchpad.
  
* Fully refactored :command:`ipcluster` command line program for starting
  IPython clusters.  This new version is a complete rewrite and 1) is fully
  cross platform (we now use Twisted's process management), 2) has much
  improved performance, 3) uses subcommands for different types of clusters, 4)
  uses argparse for parsing command line options, 5) has better support for
  starting clusters using :command:`mpirun`, 6) has experimental support for
  starting engines using PBS.  It can also reuse FURL files, by appropriately
  passing options to its subcommands.  However, this new version of ipcluster
  should be considered a technology preview.  We plan on changing the API in
  significant ways before it is final.

* Full description of the security model added to the docs.

* cd completer: show bookmarks if no other completions are available.

* sh profile: easy way to give 'title' to prompt: assign to variable
  '_prompt_title'. It looks like this::
      
        [~]|1> _prompt_title = 'sudo!'
        sudo![~]|2>

* %edit: If you do '%edit pasted_block', pasted_block variable gets updated
  with new data (so repeated editing makes sense)

.. _Numpy Documentation Standard: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard

.. _argparse: http://code.google.com/p/argparse/

Bug fixes
---------

* Fix #368719, removed top-level debian/ directory to make the job of Debian
  packagers easier.
  
* Fix #291143 by including man pages contributed by Stephan Peijnik from the
  Debian project.

* Fix #358202, effectively a race condition, by properly synchronizing file
  creation at cluster startup time.

* `%timeit` now handles correctly functions that take a long time to execute
  even the first time, by not repeating them.

* Fix #239054, releasing of references after exiting.

* Fix #341726, thanks to Alexander Clausen.

* Fix #269966.  This long-standing and very difficult bug (which is actually a
  problem in Python itself) meant long-running sessions would inevitably grow
  in memory size, often with catastrophic consequences if users had large
  objects in their scripts.  Now, using `%run` repeatedly should not cause any
  memory leaks.  Special thanks to John Hunter and Sameer D'Costa for their
  help with this bug.

* Fix #295371, bug in `%history`.

* Improved support for py2exe.

* Fix #270856: IPython hangs with PyGTK

* Fix #270998: A magic with no docstring breaks the '%magic magic'

* fix #271684: -c startup commands screw up raw vs. native history

* Numerous bugs on Windows with the new ipcluster have been fixed.

* The ipengine and ipcontroller scripts now handle missing furl files
  more gracefully by giving better error messages.

* %rehashx: Aliases no longer contain dots. python3.0 binary
  will create alias python30. Fixes:
  #259716 "commands with dots in them don't work"

* %cpaste: %cpaste -r repeats the last pasted block.
  The block is assigned to pasted_block even if code
  raises exception.

* Bug #274067 'The code in get_home_dir is broken for py2exe' was
  fixed.

* Many other small bug fixes not listed here by number (see the bzr log for
  more info).
  
Backwards incompatible changes
------------------------------

* `ipykit` and related files were unmaintained and have been removed.

* The :func:`IPython.genutils.doctest_reload` does not actually call
  `reload(doctest)` anymore, as this was causing many problems with the test
  suite.  It still resets `doctest.master` to None.

* While we have not deliberately broken Python 2.4 compatibility, only minor
  testing was done with Python 2.4, while 2.5 and 2.6 were fully tested.  But
  if you encounter problems with 2.4, please do report them as bugs.

* The :command:`ipcluster` now requires a mode argument; for example to start a
  cluster on the local machine with 4 engines, you must now type::

    $ ipcluster local -n 4

* The controller now has a ``-r`` flag that needs to be used if you want to
  reuse existing furl files.  Otherwise they are deleted (the default).

* Remove ipy_leo.py. You can use :command:`easy_install ipython-extension` to
  get it.  (done to decouple it from ipython release cycle)

