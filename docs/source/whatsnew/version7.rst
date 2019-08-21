============
 7.x Series
============

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
