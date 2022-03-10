============
 7.x Series
============


.. _version 7.32:

IPython 7.32
============



Autoload magic lazily
---------------------

The ability to configure magics to be lazily loaded has been added to IPython.
See the ``ipython --help-all`` section on ``MagicsManager.lazy_magic``.
One can now use::

    c.MagicsManager.lazy_magics = {
              "my_magic": "slow.to.import",
              "my_other_magic": "also.slow",
    }

And on first use of ``%my_magic``, or corresponding cell magic, or other line magic,
the corresponding ``load_ext`` will be called just before trying to invoke the magic.

Misc
----

 - Update sphinxify  for Docrepr 0.2.0  :ghpull:`13503`.
 - Set co_name for cells run line by line (to fix debugging with Python 3.10)
   :ghpull:`13535`


Many thanks to all the contributors to this release. You can find all individual
contributions to this milestone `on github
<https://github.com/ipython/ipython/milestone/99>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.

.. _version 7.31:

IPython 7.31
============

IPython 7.31 brings a couple of backports and fixes from the 8.0 branches,
it is likely one of the last releases of the 7.x series, as 8.0 will probably be released
between this release and what would have been 7.32.

Please test 8.0 beta/rc releases in addition to this release.

This Releases:
 - Backport some fixes for Python 3.10 (:ghpull:`13412`)
 - use full-alpha transparency on dvipng rendered LaTeX (:ghpull:`13372`)

Many thanks to all the contributors to this release. You can find all individual
contributions to this milestone `on github
<https://github.com/ipython/ipython/milestone/95>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.


.. _version 7.30:

IPython 7.30
============

IPython 7.30 fixes a couple of bugs introduce in previous releases (in
particular with respect to path handling), and introduce a few features and
improvements:

Notably we will highlight :ghpull:`13267` "Document that ``%run`` can execute
notebooks and ipy scripts.", which is the first commit of Fernando Pérez since
mid 2016 (IPython 5.1). If you are new to IPython, Fernando created IPython in
2001. The other most recent contribution of Fernando to IPython itself was
May 2018, by reviewing and merging PRs. I want to note that Fernando is still
active but mostly as a mentor and leader of the whole Jupyter organisation, but
we're still happy to see him contribute code !

:ghpull:`13290` "Use sphinxify (if available) in object_inspect_mime path"
should allow richer Repr of docstrings when using jupyterlab inspector.

:ghpull:`13311` make the debugger use ``ThreadPoolExecutor`` for debugger cmdloop.
This should fix some issues/infinite loop, but let us know if you come across
any regressions. In particular this fixes issues with `kmaork/madbg <https://github.com/kmaork/madbg>`_,
a remote debugger for IPython.

Note that this is likely the ante-penultimate release of IPython 7.x as a stable
branch, as I hope to release IPython 8.0 as well as IPython 7.31 next
month/early 2022.

IPython 8.0 will drop support for Python 3.7, removed nose as a dependency, and
7.x will only get critical bug fixes with 8.x becoming the new stable. This will
not be possible without `NumFOCUS Small Development Grants
<https://numfocus.org/programs/small-development-grants>`_ Which allowed us to
hire `Nikita Kniazev <https://github.com/Kojoley>`_ who provide Python and C++
help and contracting work.


Many thanks to all the contributors to this release. You can find all individual
contributions to this milestone `on github
<https://github.com/ipython/ipython/milestone/94?closed=1>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.


.. _version 7.29:

IPython 7.29
============


IPython 7.29 brings a couple of new functionalities to IPython and a number of bugfixes.
It is one of the largest recent release, relatively speaking, with close to 15 Pull Requests.


 - fix an issue where base64 was returned instead of bytes when showing figures :ghpull:`13162`
 - fix compatibility with PyQt6, PySide 6 :ghpull:`13172`. This may be of
   interest if you are running on Apple Silicon as only qt6.2+ is natively
   compatible.
 - fix matplotlib qtagg eventloop :ghpull:`13179`
 - Multiple docs fixes, typos, ... etc.
 - Debugger will now exit by default on SigInt :ghpull:`13218`, this will be
   useful in notebook/lab if you forgot to exit the debugger. "Interrupt Kernel"
   will now exist the debugger.

It give Pdb the ability to skip code in decorators. If functions contain a
special value names ``__debuggerskip__ = True|False``, the function will not be
stepped into, and Pdb will step into lower frames only if the value is set to
``False``. The exact behavior is still likely to have corner cases and will be
refined in subsequent releases. Feedback welcome. See the debugger module
documentation for more info. Thanks to the `D. E. Shaw
group <https://deshaw.com/>`__ for funding this feature.

The main branch of IPython is receiving a number of changes as we received a
`NumFOCUS SDG <https://numfocus.org/programs/small-development-grants>`__
($4800), to help us finish replacing ``nose`` by ``pytest``, and make IPython
future proof with an 8.0 release.


Many thanks to all the contributors to this release. You can find all individual
contributions to this milestone `on github
<https://github.com/ipython/ipython/milestone/93>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.


.. _version 7.28:

IPython 7.28
============


IPython 7.28 is again a minor release that mostly bring bugfixes, and couple of
improvement. Many thanks to MrMino, who again did all the work this month, and
made a number of documentation improvements.

Here is a non-exhaustive list of changes,

Fixes:

 - async with doesn't allow newlines :ghpull:`13090`
 - Dynamically changing to vi mode via %config magic) :ghpull:`13091`

Virtualenv handling fixes:

 - init_virtualenv now uses Pathlib :ghpull:`12548`
 - Fix Improper path comparison of virtualenv directories :ghpull:`13140`
 - Fix virtual environment user warning for lower case pathes :ghpull:`13094`
 - Adapt to all sorts of drive names for cygwin :ghpull:`13153`

New Features:

 - enable autoplay in embed YouTube player :ghpull:`13133`

 Documentation:

 - Fix formatting for the core.interactiveshell documentation :ghpull:`13118`
 - Fix broken ipyparallel's refs :ghpull:`13138`
 - Improve formatting of %time documentation :ghpull:`13125`
 - Reword the YouTubeVideo autoplay WN :ghpull:`13147`


Highlighted features
--------------------


``YouTubeVideo`` autoplay and the ability to add extra attributes to ``IFrame``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add any extra attributes to the ``<iframe>`` tag using the new
``extras`` argument in the ``IFrame`` class. For example::

    In [1]: from IPython.display import IFrame

    In [2]: IFrame(src="src", width=300, height=300, extras=['loading="eager"'])

The above cells will result in the following HTML code being displayed in a
notebook::

    <iframe
        width="300"
        height="300"
        src="src"
        frameborder="0"
        allowfullscreen
        loading="eager"
    ></iframe>

Related to the above, the ``YouTubeVideo`` class now takes an
``allow_autoplay`` flag, which sets up the iframe of the embedded YouTube video
such that it allows autoplay.

.. note::
    Whether this works depends on the autoplay policy of the browser rendering
    the HTML allowing it. It also could get blocked by some browser extensions.

Try it out!
::

    In [1]: from IPython.display import YouTubeVideo

    In [2]: YouTubeVideo("dQw4w9WgXcQ", allow_autoplay=True)



Thanks
------

Many thanks to all the contributors to this release. You can find all individual
contributions to this milestone `on github
<https://github.com/ipython/ipython/milestone/92>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.


.. _version 7.27:

IPython 7.27
============

IPython 7.27 is a minor release that fixes a couple of issues and compatibility.

- Add support for GTK4 :ghpull:`131011`
- Add support for Qt6 :ghpull:`13085`
- Fix an issue with pip magic on windows :ghpull:`13093`

Thanks
------

Many thanks to all the contributors to this release. You can find all individual
contributions to this milestone `on github
<https://github.com/ipython/ipython/milestone/91>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.

.. _version 7.26:

IPython 7.26
============

IPython 7.26 is a minor release that fixes a couple of issues, updates in API
and Copyright/Licenses issues around various part of the codebase.

We'll highlight `this issue <https://github.com/ipython/ipython/issues/13039>`
pointing out we were including and refereeing to code from Stack Overflow which
was CC-BY-SA, hence incompatible with the BSD license of IPython. This lead us
to a rewriting of the corresponding logic which in our case was done in a more
efficient way (in our case we were searching string prefixes instead of full
strings).

You will notice also a number of documentation improvements and cleanup.

Of particular interest are the following Pull-requests:


 - The IPython directive now uses Sphinx logging for warnings. :ghpull:`13030`.
 - Add expiry days option to pastebin magic and change http protocol to https.
   :ghpull:`13056`
 - Make Ipython.utils.timing work with jupyterlite :ghpull:`13050`.

Pastebin magic expiry days option
---------------------------------

The Pastebin magic now has ``-e`` option to determine 
the number of days for paste expiration. For example
the paste that created with ``%pastebin -e 20 1`` magic will
be available for next 20 days.





Thanks
------

Many thanks to all the contributors to this release and in particular MrMino who
is doing most of the work those days. You can find all individual contributions
to this milestone `on github <https://github.com/ipython/ipython/milestone/90>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.


.. _version 7.25:

IPython 7.25
============

IPython 7.25 is a minor release that contains a single bugfix, which is highly
recommended for all users of ipdb, ipython debugger %debug magic and similar.

Issuing commands like ``where`` from within the debugger would reset the
local variables changes made by the user. It is interesting to look at the root
cause of the issue as accessing an attribute (``frame.f_locals``) would trigger
this side effects.

Thanks in particular to the patience from the reporters at D.E. Shaw for their
initial bug report that was due to a similar coding oversight in an extension,
and who took time to debug and narrow down the problem.

Thanks
------

Many thanks to all the contributors to this release you can find all individual
contributions to this milestone `on github <https://github.com/ipython/ipython/milestone/89>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries.


.. _version 7.24:

IPython 7.24
============

Third release of IPython for 2021, mostly containing bug fixes. A couple of not
typical updates:

Misc
----


 - Fix an issue where ``%recall`` would both succeeded and print an error message
   it failed. :ghpull:`12952`
 - Drop support for NumPy 1.16 – practically has no effect beyond indicating in
   package metadata that we do not support it. :ghpull:`12937`

Debugger improvements
---------------------

The debugger (and ``%debug`` magic) have been improved and can skip or hide frames
originating from files that are not writable to the user, as these are less
likely to be the source of errors, or be part of system files this can be a useful
addition when debugging long errors.

In addition to the global ``skip_hidden True|False`` command, the debugger has
gained finer grained control of predicates as to whether to a frame should be
considered hidden. So far 3 predicates are available :

  - ``tbhide``: frames containing the local variable ``__tracebackhide__`` set to
    True.
  - ``readonly``: frames originating from readonly files, set to False.
  - ``ipython_internal``: frames that are likely to be from IPython internal
    code, set to True.

You can toggle individual predicates during a session with

.. code-block::

   ipdb> skip_predicates readonly True

Read-only files will now be considered hidden frames.


You can call ``skip_predicates`` without arguments to see the states of current
predicates:

.. code-block::

    ipdb> skip_predicates
    current predicates:
        tbhide : True
        readonly : False
        ipython_internal : True

If all predicates are set to ``False``,  ``skip_hidden`` will practically have
no effect. We attempt to warn you when all predicates are False.

Note that the ``readonly`` predicate may increase disk access as we check for
file access permission for all frames on many command invocation, but is usually
cached by operating systems. Let us know if you encounter any issues.

As the IPython debugger does not use the traitlets infrastructure for
configuration, by editing your ``.pdbrc`` files and appending commands you would
like to be executed just before entering the interactive prompt. For example:


.. code::

    # file : ~/.pdbrc
    skip_predicates readonly True
    skip_predicates tbhide False

Will hide read only frames by default and show frames marked with
``__tracebackhide__``.




Thanks
------

Many thanks to all the contributors to this release you can find all individual
contributions to this milestone `on github <https://github.com/ipython/ipython/milestone/87>`__.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`__ for sponsoring
work on IPython and related libraries, in particular above mentioned
improvements to the debugger.




.. _version 7.23:

IPython 7.23 and 7.23.1
=======================


Third release of IPython for 2021, mostly containing bug fixes. A couple of not
typical updates:

 - We moved to GitHub actions away from Travis-CI, the transition may not be
   100% complete (not testing on nightly anymore), but as we ran out of
   Travis-Ci hours on the IPython organisation that was a necessary step.
   :ghpull:`12900`.

 - We have a new dependency: ``matplotlib-inline``, which try to extract
   matplotlib inline backend specific behavior. It is available on PyPI and
   conda-forge thus should not be a problem to upgrade to this version. If you
   are a package maintainer that might be an extra dependency to package first.
   :ghpull:`12817` (IPython 7.23.1 fix a typo that made this change fail)

In the addition/new feature category, ``display()`` now have a ``clear=True``
option to clear the display if any further outputs arrives, allowing users to
avoid having to use ``clear_output()`` directly. :ghpull:`12823`.

In bug fixes category, this release fix an issue when printing tracebacks
containing Unicode characters :ghpull:`12758`.

In code cleanup category :ghpull:`12932` remove usage of some deprecated
functionality for compatibility with Python 3.10.



Thanks
------

Many thanks to all the contributors to this release you can find all individual
contributions to this milestone `on github <https://github.com/ipython/ipython/milestone/86>`__.
In particular MrMino for responding to almost all new issues, and triaging many
of the old ones, as well as takluyver, minrk, willingc for reacting quikly when
we ran out of CI Hours.

Thanks as well to organisations, QuantStack (martinRenou and SylvainCorlay) for
extracting matplotlib inline backend into its own package, and the `D. E. Shaw group
<https://deshaw.com/>`__ for sponsoring work on IPython and related libraries.


.. _version 7.22:

IPython 7.22
============

Second release of IPython for 2021, mostly containing bug fixes. Here is a quick
rundown of the few changes.

- Fix some ``sys.excepthook`` shenanigan when embedding with qt, recommended if
  you – for example – use `napari <https://napari.org>`__. :ghpull:`12842`.
- Fix bug when using the new ipdb ``%context`` magic :ghpull:`12844`
- Couples of deprecation cleanup :ghpull:`12868`
- Update for new dpast.com api if you use the ``%pastbin`` magic. :ghpull:`12712`
- Remove support for numpy before 1.16. :ghpull:`12836`


Thanks
------

We have a new team member that you should see more often on the IPython
repository, Błażej Michalik (@MrMino) have been doing regular contributions to
IPython, and spent time replying to many issues and guiding new users to the
codebase; they now have triage permissions to the IPython repository and we'll
work toward giving them more permission in the future.

Many thanks to all the contributors to this release you can find all individual
contributions to this milestone `on github <https://github.com/ipython/ipython/milestone/84>`__.

Thanks as well to organisations, QuantStack for working on debugger
compatibility for Xeus_python, and the `D. E. Shaw group
<https://deshaw.com/>`__ for sponsoring work on IPython and related libraries.

.. _version 721:

IPython 7.21
============

IPython 7.21 is the first release we have back on schedule of one release every
month; it contains a number of minor fixes and improvements, notably, the new
context command for ipdb


New "context" command in ipdb
-----------------------------

It is now possible to change the number of lines shown in the backtrace
information in ipdb using "context" command. :ghpull:`12826`

(thanks @MrMino, there are other improvement from them on master).

Other notable changes in IPython 7.21
-------------------------------------

- Fix some issues on new osx-arm64 :ghpull:`12804`, :ghpull:`12807`. 
- Compatibility with Xeus-Python for debugger protocol, :ghpull:`12809`
- Misc docs fixes for compatibility and uniformity with Numpydoc.
  :ghpull:`12824`


Thanks
------

Many thanks to all the contributors to this release you can find all individual
contribution to this milestone `on github <https://github.com/ipython/ipython/milestone/83>`__.


.. _version 720:

IPython 7.20
============

IPython 7.20 is the accumulation of 3 month of work on IPython, spacing between
IPython release have been increased from the usual once a month for various
reason.

   - Mainly as I'm too busy and the effectively sole maintainer, and
   - Second because not much changes happened before mid December.

The main driver for this release was the new version of Jedi 0.18 breaking API;
which was taken care of in the master branch early in 2020 but not in 7.x as I
though that by now 8.0 would be out.

The inclusion of a resolver in pip did not help and actually made things worse.
If usually I would have simply pinned Jedi to ``<0.18``; this is not a solution
anymore as now pip is free to install Jedi 0.18, and downgrade IPython.

I'll do my best to keep the regular release, but as the 8.0-dev branch and 7.x
are starting to diverge this is becoming difficult in particular with my limited
time, so if you have any cycles to spare I'll appreciate your help to respond to
issues and pushing 8.0 forward.

Here are thus some of the changes for IPython 7.20.

  - Support for PyQt5 >= 5.11 :ghpull:`12715`
  - ``%reset`` remove imports more agressively :ghpull:`12718`
  - fix the ``%conda`` magic :ghpull:`12739`
  - compatibility with Jedi 0.18, and bump minimum Jedi version. :ghpull:`12793`


.. _version 719:

IPython 7.19
============

IPython 7.19 accumulative two month of works, bug fixes and improvements, there
was exceptionally no release last month.

  - Fix to restore the ability to specify more than one extension using command
    line flags when using traitlets 5.0 :ghpull:`12543`
  - Docs docs formatting that make the install commands work on zsh
    :ghpull:`12587`
  - Always display the last frame in tracebacks even if hidden with
    ``__tracebackhide__`` :ghpull:`12601`
  - Avoid an issue where a callback can be registered multiple times.
    :ghpull:`12625`
  - Avoid an issue in debugger mode where frames changes could be lost.
    :ghpull:`12627`

  - Never hide the frames that invoke a debugger, even if marked as hidden by
    ``__tracebackhide__`` :ghpull:`12631`
  - Fix calling the debugger in a recursive manner :ghpull:`12659`


A number of code changes have landed on master and we are getting close to
enough new features and codebase improvement that a 8.0 start to make sens.
For downstream packages, please start working on migrating downstream testing
away from iptest and using pytest, as nose will not work on Python 3.10 and we
will likely start removing it as a dependency for testing.

.. _version 718:

IPython 7.18
============

IPython 7.18 is a minor release that mostly contains bugfixes.

 - ``CRLF`` is now handled by magics my default; solving some issues due to copy
   pasting on windows. :ghpull:`12475`

 - Requiring pexpect ``>=4.3`` as we are Python 3.7+ only and earlier version of
   pexpect will be incompatible. :ghpull:`12510`

 - Minimum jedi version is now 0.16. :ghpull:`12488`



.. _version 717:

IPython 7.17
============

IPython 7.17 brings a couple of new improvements to API and a couple of user
facing changes to make the terminal experience more user friendly.

:ghpull:`12407` introduces the ability to pass extra argument to the IPython
debugger class; this is to help a new project from ``kmaork``
(https://github.com/kmaork/madbg) to feature a fully remote debugger.

:ghpull:`12410` finally remove support for 3.6, while the codebase is still
technically compatible; IPython will not install on Python 3.6.

lots of work on the debugger and hidden frames from ``@impact27`` in
:ghpull:`12437`, :ghpull:`12445`, :ghpull:`12460` and in particular
:ghpull:`12453` which make the debug magic more robust at handling spaces.

Biggest API addition is code transformation which is done before code execution;
IPython allows a number of hooks to catch non-valid Python syntax (magic, prompt
stripping...etc). Transformers are usually called many time; typically:

 - When trying to figure out whether the code is complete and valid (should we
   insert a new line or execute ?)
 - During actual code execution pass before giving the code to Python's
   ``exec``.

This lead to issues when transformer might have had side effects; or do external
queries. Starting with IPython 7.17 you can expect your transformer to be called
less time.

Input transformers are now called only once in the execution path of
`InteractiveShell`, allowing to register transformer that potentially have side
effects (note that this is not recommended). Internal methods `should_run_async`, and
`run_cell_async` now take a recommended optional `transformed_cell`, and
`preprocessing_exc_tuple` parameters that will become mandatory at some point in
the future; that is to say cells need to be explicitly transformed to be valid
Python syntax ahead of trying to run them. :ghpull:`12440`;

``input_transformers`` can now also have an attribute ``has_side_effects`` set
to `True`, when this attribute is present; this  will prevent the transformers
from being ran when IPython is trying to guess whether the user input is
complete. Note that this may means you will need to explicitly execute in some
case where your transformations are now not ran; but will not affect users with
no custom extensions.


API Changes
-----------

Change of API and exposed objects automatically detected using `frappuccino
<https://pypi.org/project/frappuccino/>`_


 The following items are new since 7.16.0::

     + IPython.core.interactiveshell.InteractiveShell.get_local_scope(self, stack_depth)

 The following signatures differ since 7.16.0::

     - IPython.core.interactiveshell.InteractiveShell.run_cell_async(self, raw_cell, store_history=False, silent=False, shell_futures=True)
     + IPython.core.interactiveshell.InteractiveShell.run_cell_async(self, raw_cell, store_history=False, silent=False, shell_futures=True, *, transformed_cell=None, preprocessing_exc_tuple=None)

     - IPython.core.interactiveshell.InteractiveShell.should_run_async(self, raw_cell)
     + IPython.core.interactiveshell.InteractiveShell.should_run_async(self, raw_cell, *, transformed_cell=None, preprocessing_exc_tuple=None)

     - IPython.terminal.debugger.TerminalPdb.pt_init(self)
     + IPython.terminal.debugger.TerminalPdb.pt_init(self, pt_session_options=None)

This method was added::

     + IPython.core.interactiveshell.InteractiveShell.get_local_scope

Which is now also present on subclasses::

     + IPython.terminal.embed.InteractiveShellEmbed.get_local_scope
     + IPython.terminal.interactiveshell.TerminalInteractiveShell.get_local_scope


.. _version 716:

IPython 7.16.1, 7.16.2
======================

IPython 7.16.1 was release immediately after 7.16.0 to fix a conda packaging issue.
The source is identical to 7.16.0 but the file permissions in the tar are different.

IPython 7.16.2 pins jedi dependency to "<=0.17.2" which should prevent some
issues for users still on python 3.6. This may not be sufficient as pip may
still allow to downgrade IPython.

Compatibility with Jedi > 0.17.2 was not added as this would have meant bumping
the minimal version to >0.16.

IPython 7.16
============


The default traceback mode will now skip frames that are marked with
``__tracebackhide__ = True`` and show how many traceback frames have been
skipped. This can be toggled by using :magic:`xmode` with the ``--show`` or
``--hide`` attribute. It will have no effect on non verbose traceback modes.

The ipython debugger also now understands ``__tracebackhide__`` as well and will
skip hidden frames when displaying. Movement up and down the stack will skip the
hidden frames and will show how many frames were hidden. Internal IPython frames
are also now hidden by default. The behavior can be changed with the
``skip_hidden`` while in the debugger, command and accepts "yes", "no", "true"
and "false" case insensitive parameters.


Misc Noticeable changes:
------------------------

- Exceptions are now (re)raised when running notebooks via the :magic:`%run`, helping to catch issues in workflows and
  pipelines. :ghpull:`12301`
- Fix inputhook for qt 5.15.0 :ghpull:`12355`
- Fix wx inputhook :ghpull:`12375`
- Add handling for malformed pathext env var (Windows) :ghpull:`12367`
- use $SHELL in system_piped :ghpull:`12360` for uniform behavior with
  ipykernel.

Reproducible Build
------------------

IPython 7.15 reproducible build did not work, so we try again this month
:ghpull:`12358`.


API Changes
-----------

Change of API and exposed objects automatically detected using `frappuccino
<https://pypi.org/project/frappuccino/>`_ (still in beta):


The following items are new and mostly related to understanding ``__tracebackhide__``::

    + IPython.core.debugger.Pdb.do_down(self, arg)
    + IPython.core.debugger.Pdb.do_skip_hidden(self, arg)
    + IPython.core.debugger.Pdb.do_up(self, arg)
    + IPython.core.debugger.Pdb.hidden_frames(self, stack)
    + IPython.core.debugger.Pdb.stop_here(self, frame)


The following items have been removed::

    - IPython.core.debugger.Pdb.new_do_down
    - IPython.core.debugger.Pdb.new_do_up

Those were implementation details.


.. _version 715:

IPython 7.15
============

IPython 7.15 brings a number of bug fixes and user facing improvements.

Misc Noticeable changes:
------------------------

 - Long completion name have better elision in terminal :ghpull:`12284`
 - I've started to test on Python 3.9 :ghpull:`12307` and fix some errors.
 - Hi DPI scaling of figures when using qt eventloop :ghpull:`12314`
 - Document the ability to have systemwide configuration for IPython.
   :ghpull:`12328`
 - Fix issues with input autoformatting :ghpull:`12336`
 - ``IPython.core.debugger.Pdb`` is now interruptible (:ghpull:`12168`, in 7.14
   but forgotten in release notes)
 - Video HTML attributes (:ghpull:`12212`, in 7.14 but forgotten in release
   notes)

Reproducible Build
------------------

Starting with IPython 7.15, I am attempting to provide reproducible builds,
that is to say you should be able from the source tree to generate an sdist
and wheel that are identical byte for byte with the publish version on PyPI.

I've only tested on a couple of machines so far and the process is relatively
straightforward, so this mean that IPython not only have a deterministic build
process, but also I have either removed, or put under control all effects of
the build environments on the final artifact.  I encourage you to attempt the
build process on your machine as documented in :ref:`core_developer_guide`
and let me know if you do not obtain an identical artifact.

While reproducible builds is critical to check that the supply chain of (open
source) software has not been compromised, it can also help to speedup many
of the build processes in large environment (conda, apt...) by allowing
better caching of intermediate build steps.

Learn more on `<https://reproducible-builds.org/>`_. `Reflections on trusting
trust <https://dl.acm.org/doi/10.1145/358198.358210>`_ is also one of the
cornerstone and recommended reads on this subject.

.. note::

   The build commit from which the sdist is generated is also `signed
   <https://en.wikipedia.org/wiki/Digital_signature>`_, so you should be able to
   check it has not been compromised, and the git repository is a `merkle-tree
   <https://en.wikipedia.org/wiki/Merkle_tree>`_, you can check the consistency
   with `git-fsck <https://git-scm.com/docs/git-fsck>`_ which you likely `want
   to enable by default
   <https://gist.github.com/mbbx6spp/14b86437e794bffb4120>`_.

NEP29: Last version to support Python 3.6
-----------------------------------------

IPython 7.15 will be the Last IPython version to officially support Python
3.6, as stated by `NumPy Enhancement Proposal 29
<https://numpy.org/neps/nep-0029-deprecation_policy.html>`_. Starting with
next minor version of IPython I may stop testing on Python 3.6 and may stop
publishing release artifacts that install on Python 3.6

Highlighted features
--------------------

Highlighted features are not new, but seem to not be widely known, this
section will help you discover in more narrative form what you can do with
IPython.

Increase Tab Completion Menu Height
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In terminal IPython it is possible to increase the hight of the tab-completion
menu. To do so set the value of
:configtrait:`TerminalInteractiveShell.space_for_menu`, this will reserve more
space at the bottom of the screen for various kind of menus in IPython including
tab completion and searching in history. 

Autoformat Code in the terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a preferred code formatter, you can configure IPython to
reformat your code. Set the value of
:configtrait:`TerminalInteractiveShell.autoformatter` to for example ``'black'``
and IPython will auto format your code when possible.


.. _version 714:

IPython 7.14
============

IPython  7.14 is a minor release that fix a couple of bugs and prepare
compatibility with new or future versions of some libraries. 

Important changes:
------------------

 - Fix compatibility with Sphinx 3+ :ghpull:`12235`
 - Remove deprecated matplotlib parameter usage, compatibility with matplotlib
   3.3+ :`122250`

Misc Changes
------------

 - set ``.py`` extension when editing current buffer in vi/emacs. :ghpull:`12167`
 - support for unicode identifiers in ``?``/``??`` :ghpull:`12208`
 - add extra options to the ``Video`` Rich objects :ghpull:`12212`
 - add pretty-printing to ``SimpleNamespace`` :ghpull:`12230`

IPython.core.debugger.Pdb is now interruptible
----------------------------------------------

A ``KeyboardInterrupt`` will now interrupt IPython's extended debugger, in order to make Jupyter able to interrupt it. (:ghpull:`12168`)

Video HTML attributes
---------------------

Add an option to `IPython.display.Video` to change the attributes of the HTML display of the video (:ghpull:`12212`)


Pending deprecated imports
--------------------------

Many object present in ``IPython.core.display`` are there for internal use only,
and should  already been imported from ``IPython.display`` by users and external
libraries. Trying to import those from ``IPython.core.display`` is still possible
but will trigger a
deprecation warning in later versions of IPython and will become errors in the
future. 

This will simplify compatibility with other Python kernels (like Xeus-Python),
and simplify code base. 




.. _version 713:

IPython 7.13
============

IPython 7.13 is the final release of the 7.x branch since master is diverging
toward an 8.0. Exiting new features have already been merged in 8.0 and will
not be available on the 7.x branch. All the changes below have been backported
from the master branch.


 - Fix inability to run PDB when inside an event loop :ghpull:`12141`
 - Fix ability to interrupt some processes on windows :ghpull:`12137`
 - Fix debugger shortcuts :ghpull:`12132`
 - improve tab completion when inside a string by removing irrelevant elements :ghpull:`12128`
 - Fix display of filename tab completion when the path is long :ghpull:`12122`
 - Many removal of Python 2 specific code path :ghpull:`12110`
 - displaying wav files do not require NumPy anymore, and is 5x to 30x faster :ghpull:`12113`

See the list of all closed issues and pull request on `github
<https://github.com/ipython/ipython/pulls?q=is%3Aclosed+milestone%3A7.13>`_.

.. _version 712:

IPython 7.12
============

IPython 7.12 is a minor update that mostly brings code cleanup, removal of
longtime deprecated function and a couple update to documentation cleanup as well.

Notable changes are the following:

 - Exit non-zero when ipython is given a file path to run that doesn't exist :ghpull:`12074`
 - Test PR on ARM64 with Travis-CI :ghpull:`12073`
 - Update CI to work with latest Pytest :ghpull:`12086`
 - Add infrastructure to run ipykernel eventloop via trio :ghpull:`12097`
 - Support git blame ignore revs :ghpull:`12091`
 - Start multi-line ``__repr__`` s on their own line :ghpull:`12099`

.. _version 7111:

IPython 7.11.1
==============

A couple of deprecated functions (no-op) have been reintroduces in py3compat as
Cython was still relying on them, and will be removed in a couple of versions.

.. _version 711:

IPython 7.11
============

IPython 7.11 received a couple of compatibility fixes and code cleanup.

A number of function in the ``py3compat`` have been removed; a number of types
in the IPython code base are now non-ambiguous and now always ``unicode``
instead of ``Union[Unicode,bytes]``; many of the relevant code path have thus
been simplified/cleaned and types annotation added.

IPython support several verbosity level from exceptions. ``xmode plain`` now
support chained exceptions. :ghpull:`11999`

We are starting to remove ``shell=True`` in some usages of subprocess. While not directly
a security issue (as IPython is made to run arbitrary code anyway) it is not good
practice and we'd like to show the example. :ghissue:`12023`. This discussion
was started by ``@mschwager`` thanks to a new auditing tool they are working on
with duo-labs (`dlint <https://github.com/duo-labs/dlint>`_).

Work around some bugs in Python 3.9 tokenizer :ghpull:`12057`

IPython will now print its version after a crash. :ghpull:`11986`

This is likely the last release from the 7.x series that will see new feature.
The master branch will soon accept large code changes and thrilling new
features; the 7.x branch will only start to accept critical bug fixes, and
update dependencies.

.. _version 7102:

IPython 7.10.2
==============

IPython 7.10.2 fix a couple of extra incompatibility between IPython, ipdb,
asyncio and Prompt Toolkit 3.

.. _version 7101:

IPython 7.10.1
==============

IPython 7.10.1 fix a couple of incompatibilities with Prompt toolkit 3 (please
update Prompt toolkit to 3.0.2 at least), and fixes some interaction with
headless IPython.

.. _version 7100:

IPython 7.10.0
==============

IPython 7.10 is the first double digit minor release in the  last decade, and
first since the release of IPython 1.0, previous double digit minor release was
in August 2009.

We've been trying to give you regular release on the last Friday of every month
for a guaranty of rapid access to bug fixes and new features.

Unlike the previous first few releases that have seen only a couple of code
changes, 7.10 bring a number of changes, new features and bugfixes.

Stop Support for Python 3.5 – Adopt NEP 29
------------------------------------------

IPython has decided to follow the informational `NEP 29
<https://numpy.org/neps/nep-0029-deprecation_policy.html>`_ which layout a clear
policy as to which version of (C)Python and NumPy are supported.

We thus dropped support for Python 3.5, and cleaned up a number of code path
that were Python-version dependant. If you are on 3.5 or earlier pip should
automatically give you the latest compatible version of IPython so you do not
need to pin to a given version.

Support for Prompt Toolkit 3.0
------------------------------

Prompt Toolkit 3.0 was release a week before IPython 7.10 and introduces a few
breaking changes. We believe IPython 7.10 should be compatible with both Prompt
Toolkit 2.x and 3.x, though it has not been extensively tested with 3.x so
please report any issues.


Prompt Rendering Performance improvements
-----------------------------------------

Pull Request :ghpull:`11933` introduced an optimisation in the prompt rendering
logic that should decrease the resource usage of IPython when using the
_default_ configuration but could potentially introduce a regression of
functionalities if you are using a custom prompt.

We know assume if you haven't changed the default keybindings that the prompt
**will not change** during the duration of your input – which is for example
not true when using vi insert mode that switches between `[ins]` and `[nor]`
for the current mode.

If you are experiencing any issue let us know.

Code autoformatting
-------------------

The IPython terminal can now auto format your code just before entering a new
line or executing a command. To do so use the
``--TerminalInteractiveShell.autoformatter`` option and set it to ``'black'``;
if black is installed IPython will use black to format your code when possible.

IPython cannot always properly format your code; in particular it will
auto formatting with *black* will only work if:

   - Your code does not contains magics or special python syntax.

   - There is no code after your cursor.

The Black API is also still in motion; so this may not work with all versions of
black.

It should be possible to register custom formatter, though the API is till in
flux.

Arbitrary Mimetypes Handing in Terminal (Aka inline images in terminal)
-----------------------------------------------------------------------

When using IPython terminal it is now possible to register function to handle
arbitrary mimetypes. While rendering non-text based representation was possible in
many jupyter frontend; it was not possible in terminal IPython, as usually
terminal are limited to displaying text. As many terminal these days provide
escape sequences to display non-text; bringing this loved feature to IPython CLI
made a lot of sens. This functionality will not only allow inline images; but
allow opening of external program; for example ``mplayer`` to "display" sound
files.

So far only the hooks necessary for this are in place, but no default mime
renderers added; so inline images will only be available via extensions. We will
progressively enable these features by default in the next few releases, and
contribution is welcomed.

We welcome any feedback on the API. See :ref:`shell_mimerenderer` for more
informations.

This is originally based on work form in :ghpull:`10610` from @stephanh42
started over two years ago, and still a lot need to be done.

MISC
----

 - Completions can define their own ordering :ghpull:`11855`
 - Enable Plotting in the same cell than the one that import matplotlib
   :ghpull:`11916`
 - Allow to store and restore multiple variables at once :ghpull:`11930`

You can see `all pull-requests <https://github.com/ipython/ipython/pulls?q=is%3Apr+milestone%3A7.10+is%3Aclosed>`_ for this release.

API Changes
-----------

Change of API and exposed objects automatically detected using `frappuccino <https://pypi.org/project/frappuccino/>`_ (still in beta):

The following items are new in IPython 7.10::

    + IPython.terminal.shortcuts.reformat_text_before_cursor(buffer, document, shell)
    + IPython.terminal.interactiveshell.PTK3
    + IPython.terminal.interactiveshell.black_reformat_handler(text_before_cursor)
    + IPython.terminal.prompts.RichPromptDisplayHook.write_format_data(self, format_dict, md_dict='None')

The following items have been removed in 7.10::

    - IPython.lib.pretty.DICT_IS_ORDERED

The following signatures differ between versions::

    - IPython.extensions.storemagic.restore_aliases(ip)
    + IPython.extensions.storemagic.restore_aliases(ip, alias='None')

Special Thanks
--------------

 - @stephanh42 who started the work on inline images in terminal 2 years ago
 - @augustogoulart who spent a lot of time triaging issues and responding to
   users.
 - @con-f-use who is my (@Carreau) first sponsor on GitHub, as a reminder if you
   like IPython, Jupyter and many other library of the SciPy stack you can
   donate to numfocus.org non profit

.. _version 790:

IPython 7.9.0
=============

IPython 7.9 is a small release with a couple of improvement and bug fixes.

 - Xterm terminal title should be restored on exit :ghpull:`11910`
 - special variables ``_``,``__``, ``___`` are not set anymore when cache size
   is 0 or less.  :ghpull:`11877`
 - Autoreload should have regained some speed by using a new heuristic logic to
   find all objects needing reload. This should avoid large objects traversal
   like pandas dataframes. :ghpull:`11876`
 - Get ready for Python 4. :ghpull:`11874`
 - `%env` Magic now has heuristic to hide potentially sensitive values :ghpull:`11896`

This is a small release despite a number of Pull Request Pending that need to
be reviewed/worked on. Many of the core developers have been busy outside of
IPython/Jupyter and we thanks all contributor for their patience; we'll work on
these as soon as we have time.


.. _version780:

IPython 7.8.0
=============

IPython 7.8.0 contain a few bugfix and 2 new APIs:

 - Enable changing the font color for LaTeX rendering :ghpull:`11840`
 - and Re-Expose some PDB API (see below)

Expose Pdb API
--------------

Expose the built-in ``pdb.Pdb`` API. ``Pdb`` constructor arguments are generically
exposed, regardless of python version.
Newly exposed arguments:

- ``skip`` - Python 3.1+
- ``nosiginnt`` - Python 3.2+
- ``readrc`` - Python 3.6+

Try it out::

    from IPython.terminal.debugger import TerminalPdb
    pdb = TerminalPdb(skip=["skipthismodule"])


See :ghpull:`11840`

.. _version770:

IPython 7.7.0
=============

IPython 7.7.0 contain multiple bug fixes and documentation updates; Here are a
few of the outstanding issue fixed:

   - Fix a bug introduced in 7.6 where the ``%matplotlib`` magic would fail on
     previously acceptable arguments :ghpull:`11814`.
   - Fix the manage location on freebsd :ghpull:`11808`.
   - Fix error message about aliases after ``%reset`` call in ipykernel
     :ghpull:`11806`
   - Fix Duplication completions in emacs :ghpull:`11803`

We are planning to adopt `NEP29 <https://github.com/numpy/numpy/pull/14086>`_
(still currently in draft) which may make this minor version of IPython the
last one to support Python 3.5 and will make the code base more aggressive
toward removing compatibility with older versions of Python.

GitHub now support to give only "Triage" permissions to users; if you'd like to
help close stale issues and labels issues please reach to us with your GitHub
Username and we'll add you to the triage team. It is a great way to start
contributing and a path toward getting commit rights.

.. _version761:

IPython 7.6.1
=============

IPython 7.6.1 contain a critical bugfix in the ``%timeit`` magic, which would
crash on some inputs as a side effect of :ghpull:`11716`. See :ghpull:`11812`


.. _whatsnew760:

IPython 7.6.0
=============

IPython 7.6.0 contains a couple of bug fixes and number of small features
additions as well as some compatibility with the current development version of
Python 3.8.

   - Add a ``-l`` option to :magic:`psearch` to list the available search
     types. :ghpull:`11672`
   - Support ``PathLike`` for ``DisplayObject`` and ``Image``. :ghpull:`11764`
   - Configurability of timeout in the test suite for slow platforms.
     :ghpull:`11756`
   - Accept any casing for matplotlib backend. :ghpull:`121748`
   - Properly skip test that requires numpy to be installed :ghpull:`11723`
   - More support for Python 3.8 and positional only arguments (pep570)
     :ghpull:`11720`
   - Unicode names for the completion are loaded lazily on first use which
     should decrease startup time. :ghpull:`11693`
   - Autoreload now update the types of reloaded objects; this for example allow
     pickling of reloaded objects. :ghpull:`11644`
   - Fix a bug where ``%%time`` magic would suppress cell output. :ghpull:`11716`


Prepare migration to pytest (instead of nose) for testing
---------------------------------------------------------

Most of the work between 7.5 and 7.6 was to prepare the migration from our
testing framework to pytest. Most of the test suite should now work by simply
issuing ``pytest`` from the root of the repository.

The migration to pytest is just at its beginning. Many of our test still rely
on IPython-specific plugins for nose using pytest (doctest using IPython syntax
is one example of this where test appear as "passing", while no code has been
ran). Many test also need to be updated like ``yield-test`` to be properly
parametrized tests.

Migration to pytest allowed me to discover a number of issues in our test
suite; which was hiding a number of subtle issues – or not actually running
some of the tests in our test suite – I have thus corrected many of those; like
improperly closed resources; or used of deprecated features. I also made use of
the ``pytest --durations=...`` to find some of our slowest test and speed them
up (our test suite can now be up to 10% faster). Pytest as also a variety of
plugins and flags which will make the code quality of IPython and the testing
experience better.

Misc
----

We skipped the release of 7.6 at the end of May, but will attempt to get back
on schedule. We are starting to think about making introducing backward
incompatible change and start the 8.0 series.

Special Thanks to Gabriel (@gpotter2 on GitHub), who among other took care many
of the remaining task for 7.4 and 7.5, like updating the website.

.. _whatsnew750:

IPython 7.5.0
=============

IPython 7.5.0 consist mostly of bug-fixes, and documentation updates, with one
minor new feature. The `Audio` display element can now be assigned an element
id when displayed in browser. See :ghpull:`11670`

The major outstanding bug fix correct a change of behavior that was introduce
in 7.4.0 where some cell magics would not be able to access or modify global
scope when using the ``@needs_local_scope`` decorator. This was typically
encountered with the ``%%time`` and ``%%timeit`` magics. See :ghissue:`11659`
and :ghpull:`11698`.

.. _whatsnew740:

IPython 7.4.0
=============

Unicode name completions
------------------------

Previously, we provided completion for a unicode name with its relative symbol.
With this, now IPython provides complete suggestions to unicode name symbols.

As on the PR, if user types ``\LAT<tab>``, IPython provides a list of
possible completions. In this case, it would be something like::

   'LATIN CAPITAL LETTER A',
   'LATIN CAPITAL LETTER B',
   'LATIN CAPITAL LETTER C',
   'LATIN CAPITAL LETTER D',
   ....

This help to type unicode character that do not have short latex aliases, and
have long unicode names. for example ``Ͱ``, ``\GREEK CAPITAL LETTER HETA``.

This feature was contributed by Luciana Marques :ghpull:`11583`.

Make audio normalization optional
---------------------------------

Added 'normalize' argument to `IPython.display.Audio`. This argument applies
when audio data is given as an array of samples. The default of `normalize=True`
preserves prior behavior of normalizing the audio to the maximum possible range.
Setting to `False` disables normalization.


Miscellaneous
-------------

 - Fix improper acceptation of ``return`` outside of functions. :ghpull:`11641`.
 - Fixed PyQt 5.11 backwards incompatibility causing sip import failure.
   :ghpull:`11613`.
 - Fix Bug where ``type?`` would crash IPython. :ghpull:`1608`.
 - Allow to apply ``@needs_local_scope`` to cell magics for convenience.
   :ghpull:`11542`.

.. _whatsnew730:

IPython 7.3.0
=============

.. _whatsnew720:

IPython 7.3.0 bring several bug fixes and small improvements that you will
described bellow. 

The biggest change to this release is the implementation of the ``%conda`` and
``%pip`` magics, that will attempt to install packages in the **current
environment**. You may still need to restart your interpreter or kernel for the
change to be taken into account, but it should simplify installation of packages
into remote environment. Installing using pip/conda from the command line is
still the prefer method.

The ``%pip`` magic was already present, but was only printing a warning; now it
will actually forward commands to pip. 

Misc bug fixes and improvements:

 - Compatibility with Python 3.8.
 - Do not expand shell variable in execution magics, and added the
   ``no_var_expand`` decorator for magic requiring a similar functionality
   :ghpull:`11516`
 - Add ``%pip`` and ``%conda`` magic :ghpull:`11524`
 - Re-initialize posix aliases after a ``%reset`` :ghpull:`11528`
 - Allow the IPython command line to run ``*.ipynb`` files :ghpull:`11529`

IPython 7.2.0
=============

IPython 7.2.0 brings minor bugfixes, improvements, and new configuration options:

 - Fix a bug preventing PySide2 GUI integration from working :ghpull:`11464`
 - Run CI on Mac OS ! :ghpull:`11471`
 - Fix IPython "Demo" mode. :ghpull:`11498`
 - Fix ``%run`` magic  with path in name :ghpull:`11499`
 - Fix: add CWD to sys.path *after* stdlib :ghpull:`11502`
 - Better rendering of signatures, especially long ones. :ghpull:`11505`
 - Re-enable jedi by default if it's installed :ghpull:`11506`
 - Add New ``minimal`` exception reporting mode (useful for educational purpose). See :ghpull:`11509`


Added ability to show subclasses when using pinfo and other utilities
---------------------------------------------------------------------

When using ``?``/``??`` on a class, IPython will now list the first 10 subclasses.

Special Thanks to Chris Mentzel of the Moore Foundation for this feature. Chris
is one of the people who played a critical role in IPython/Jupyter getting
funding.

We are grateful for all the help Chris has given us over the years,
and we're now proud to have code contributed by Chris in IPython.

OSMagics.cd_force_quiet configuration option
--------------------------------------------

You can set this option to force the %cd magic to behave as if ``-q`` was passed:
::

    In [1]: cd /
    /

    In [2]: %config OSMagics.cd_force_quiet = True

    In [3]: cd /tmp

    In [4]:

See :ghpull:`11491`

In vi editing mode, whether the prompt includes the current vi mode can now be configured
-----------------------------------------------------------------------------------------

Set the ``TerminalInteractiveShell.prompt_includes_vi_mode`` to a boolean value
(default: True) to control this feature. See :ghpull:`11492`

.. _whatsnew710:

IPython 7.1.0
=============

IPython 7.1.0 is the first minor release after 7.0.0 and mostly brings fixes to
new features, internal refactoring, and fixes for regressions that happened during the 6.x->7.x
transition. It also brings **Compatibility with Python 3.7.1**, as we're
unwillingly relying on a bug in CPython.

New Core Dev:

 - We welcome Jonathan Slenders to the commiters. Jonathan has done a fantastic
   work on prompt_toolkit, and we'd like to recognise his impact by giving him
   commit rights. :ghissue:`11397`

Notable Changes

 - Major update of "latex to unicode" tab completion map (see below)

Notable New Features:

 - Restore functionality and documentation of the **sphinx directive**, which
   is now stricter (fail on error by daefault), has new configuration options,
   has a brand new documentation page :ref:`ipython_directive` (which needs
   some cleanup). It is also now *tested* so we hope to have less regressions.
   :ghpull:`11402`

 - ``IPython.display.Video`` now supports ``width`` and ``height`` arguments,
   allowing a custom width and height to be set instead of using the video's
   width and height. :ghpull:`11353`

 - Warn when using ``HTML('<iframe>')`` instead of ``IFrame`` :ghpull:`11350`

 - Allow Dynamic switching of editing mode between vi/emacs and show
   normal/input mode in prompt when using vi. :ghpull:`11390`. Use ``%config
   TerminalInteractiveShell.editing_mode = 'vi'`` or ``%config
   TerminalInteractiveShell.editing_mode = 'emacs'`` to dynamically switch
   between modes.


Notable Fixes:

 - Fix entering of **multi-line blocks in terminal** IPython, and various
   crashes in the new input transformation machinery :ghpull:`11354`,
   :ghpull:`11356`, :ghpull:`11358`. These also fix a **Compatibility bug
   with Python 3.7.1**.

 - Fix moving through generator stack in ipdb :ghpull:`11266`

 - %Magic command arguments now support quoting. :ghpull:`11330`

 - Re-add ``rprint`` and ``rprinte`` aliases. :ghpull:`11331`

 - Remove implicit dependency on ``ipython_genutils`` :ghpull:`11317`

 - Make ``nonlocal`` raise ``SyntaxError`` instead of silently failing in async
   mode. :ghpull:`11382`

 - Fix mishandling of magics and ``= !`` assignment just after a dedent in
   nested code blocks :ghpull:`11418`

 - Fix instructions for custom shortcuts :ghpull:`11426`


Notable Internals improvements:

 - Use of ``os.scandir`` (Python 3 only) to speed up some file system operations.
   :ghpull:`11365`

 - use ``perf_counter`` instead of ``clock`` for more precise
   timing results with ``%time`` :ghpull:`11376`

Many thanks to all the contributors and in particular to ``bartskowron`` and
``tonyfast`` who handled some pretty complicated bugs in the input machinery. We
had a number of first time contributors and maybe hacktoberfest participants that
made significant contributions and helped us free some time to focus on more
complicated bugs.

You
can see all the closed issues and Merged PR, new features and fixes `here
<https://github.com/ipython/ipython/issues?utf8=%E2%9C%93&q=+is%3Aclosed+milestone%3A7.1+>`_.

Unicode Completion update
-------------------------

In IPython 7.1 the Unicode completion map has been updated and synchronized with
the Julia language.

Added and removed character characters:

 ``\jmath`` (``ȷ``), ``\\underleftrightarrow`` (U+034D, combining) have been
 added, while ``\\textasciicaron`` have been removed

Some sequences have seen their prefix removed:

 - 6 characters ``\text...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 45 characters ``\Elz...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 65 characters ``\B...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 450 characters ``\m...<tab>`` should now be inputed with ``\...<tab>`` directly,

Some sequences have seen their prefix shortened:

 - 5 characters ``\mitBbb...<tab>`` should now be inputed with ``\bbi...<tab>`` directly,
 - 52 characters ``\mit...<tab>`` should now be inputed with ``\i...<tab>`` directly,
 - 216 characters ``\mbfit...<tab>`` should now be inputed with ``\bi...<tab>`` directly,
 - 222 characters ``\mbf...<tab>`` should now be inputed with ``\b...<tab>`` directly,

A couple of characters had their sequence simplified:

 - ``ð``, type ``\dh<tab>``, instead of ``\eth<tab>``
 - ``ħ``, type ``\hbar<tab>``, instead of ``\Elzxh<tab>``
 - ``ɸ``, type ``\ltphi<tab>``, instead of ``\textphi<tab>``
 - ``ϴ``, type ``\varTheta<tab>``, instead of ``\textTheta<tab>``
 - ``ℇ``, type ``\eulermascheroni<tab>``, instead of ``\Eulerconst<tab>``
 - ``ℎ``, type ``\planck<tab>``, instead of ``\Planckconst<tab>``

 - U+0336 (COMBINING LONG STROKE OVERLAY), type ``\strike<tab>``, instead of ``\Elzbar<tab>``.

A couple of sequences have been updated:

 - ``\varepsilon`` now gives ``ɛ`` (GREEK SMALL LETTER EPSILON) instead of ``ε`` (GREEK LUNATE EPSILON SYMBOL),
 - ``\underbar`` now gives U+0331 (COMBINING MACRON BELOW) instead of U+0332 (COMBINING LOW LINE).


.. _whatsnew700:

IPython 7.0.0
=============

Released Thursday September 27th, 2018

IPython 7 includes major feature improvements.
This is also the second major version of IPython to support only
Python 3 – starting at Python 3.4. Python 2 is still community-supported
on the bugfix only 5.x branch, but we remind you that Python 2 "end of life"
is on Jan 1st 2020.

We were able to backport bug fixes to the 5.x branch thanks to our backport bot which
backported more than `70 Pull-Requests
<https://github.com/ipython/ipython/pulls?page=3&q=is%3Apr+sort%3Aupdated-desc+author%3Aapp%2Fmeeseeksdev++5.x&utf8=%E2%9C%93>`_, but there are still many PRs that required manual work. This is an area of the project where you can easily contribute by looking for `PRs that still need manual backport <https://github.com/ipython/ipython/issues?q=label%3A%22Still+Needs+Manual+Backport%22+is%3Aclosed+sort%3Aupdated-desc>`_

The IPython 6.x branch will likely not see any further release unless critical
bugs are found.

Make sure you have pip > 9.0 before upgrading. You should be able to update by running:

.. code::

    pip install ipython --upgrade

.. only:: ipydev

  If you are trying to install or update an ``alpha``, ``beta``, or ``rc``
  version, use pip ``--pre`` flag.

  .. code::

      pip install ipython --upgrade --pre


Or, if you have conda installed: 

.. code::
   
   conda install ipython



Prompt Toolkit 2.0
------------------

IPython 7.0+ now uses ``prompt_toolkit 2.0``. If you still need to use an earlier
``prompt_toolkit`` version, you may need to pin IPython to ``<7.0``.

Autowait: Asynchronous REPL
---------------------------

Staring with IPython 7.0 on Python 3.6+, IPython can automatically ``await``
top level code. You should not need to access an event loop or runner
yourself. To learn more, read the :ref:`autoawait` section of our docs, see
:ghpull:`11265`, or try the following code::

    Python 3.6.0
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.0.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import aiohttp
       ...: result = aiohttp.get('https://api.github.com')

    In [2]: response = await result
    <pause for a few 100s ms>

    In [3]: await response.json()
    Out[3]:
    {'authorizations_url': 'https://api.github.com/authorizations',
     'code_search_url': 'https://api.github.com/search/code?q={query}{&page,per_page,sort,order}',
    ...
    }

.. note::

   Async integration is experimental code, behavior may change or be removed
   between Python and IPython versions without warnings.

Integration is by default with `asyncio`, but other libraries can be configured --
like ``curio`` or ``trio`` -- to improve concurrency in the REPL::

    In [1]: %autoawait trio

    In [2]: import trio

    In [3]: async def child(i):
       ...:     print("   child %s goes to sleep"%i)
       ...:     await trio.sleep(2)
       ...:     print("   child %s wakes up"%i)

    In [4]: print('parent start')
       ...: async with trio.open_nursery() as n:
       ...:     for i in range(3):
       ...:         n.spawn(child, i)
       ...: print('parent end')
    parent start
       child 2 goes to sleep
       child 0 goes to sleep
       child 1 goes to sleep
       <about 2 seconds pause>
       child 2 wakes up
       child 1 wakes up
       child 0 wakes up
    parent end

See :ref:`autoawait` for more information.


Asynchronous code in a Notebook interface or any other frontend using the
Jupyter Protocol will require further updates to the IPykernel package.

Non-Asynchronous code
~~~~~~~~~~~~~~~~~~~~~

As the internal API of IPython is now asynchronous, IPython needs to run under
an event loop. In order to allow many workflows, (like using the :magic:`%run`
magic, or copy-pasting code that explicitly starts/stop event loop), when
top-level code is detected as not being asynchronous, IPython code is advanced
via a pseudo-synchronous runner, and may not advance pending tasks.

Change to Nested Embed
~~~~~~~~~~~~~~~~~~~~~~

The introduction of the ability to run async code had some effect on the
``IPython.embed()`` API. By default, embed will not allow you to run asynchronous
code unless an event loop is specified.

Effects on Magics
~~~~~~~~~~~~~~~~~

Some magics will not work with async until they're updated.
Contributions welcome.

Expected Future changes
~~~~~~~~~~~~~~~~~~~~~~~

We expect more internal but public IPython functions to become ``async``, and
will likely end up having a persistent event loop while IPython is running.

Thanks
~~~~~~

This release took more than a year in the making.
The code was rebased a number of
times; leading to commit authorship that may have been lost in the final
Pull-Request. Huge thanks to many people for contribution, discussion, code,
documentation, use-cases: dalejung, danielballan, ellisonbg, fperez, gnestor,
minrk, njsmith, pganssle, tacaswell, takluyver , vidartf ... And many others.


Autoreload Improvement
----------------------

The magic :magic:`%autoreload 2 <autoreload>` now captures new methods added to
classes. Earlier, only methods existing as of the initial import were being
tracked and updated.  

This new feature helps dual environment development - Jupyter+IDE - where the
code gradually moves from notebook cells to package files as it gets
structured.

**Example**: An instance of the class ``MyClass`` will be able to access the
method ``cube()`` after it is uncommented and the file ``file1.py`` is saved on
disk.


.. code::

   # notebook

   from mymodule import MyClass
   first = MyClass(5)

.. code::

   # mymodule/file1.py

   class MyClass:

       def __init__(self, a=10):
           self.a = a

       def square(self):
           print('compute square')
           return self.a*self.a

       # def cube(self):
       #     print('compute cube')
       #     return self.a*self.a*self.a




Misc
----

The autoindent feature that was deprecated in 5.x was re-enabled and
un-deprecated in :ghpull:`11257`

Make :magic:`%run -n -i ... <run>` work correctly. Earlier, if :magic:`%run` was
passed both arguments, ``-n`` would be silently ignored. See :ghpull:`10308`


The :cellmagic:`%%script` (as well as :cellmagic:`%%bash`,
:cellmagic:`%%ruby`... ) cell magics now raise by default if the return code of
the given code is non-zero (thus halting execution of further cells in a
notebook). The behavior can be disable by passing the ``--no-raise-error`` flag.


Deprecations
------------

A couple of unused functions and methods have been deprecated and will be removed
in future versions:

  - ``IPython.utils.io.raw_print_err``
  - ``IPython.utils.io.raw_print``

  
Backwards incompatible changes
------------------------------

* The API for transforming input before it is parsed as Python code has been
  completely redesigned: any custom input transformations will need to be
  rewritten. See :doc:`/config/inputtransforms` for details of the new API.
