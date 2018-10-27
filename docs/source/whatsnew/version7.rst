============
 7.x Series
============

.. _whatsnew710:

IPython 7.1.0
=============

IPython 7.1.0 is the first minor release after 7.0.0 and mostly bring fixes to
new feature, internal refactor and regressions that happen during the 6.x->7.x
transition. It also bring **Compatibility with Python 3.7.1**, as were
unwillingly relying on a bug in CPython.

New Core Dev:

 - We welcome Jonathan Slenders to the commiters. Jonathan has done a fantastic
   work on Prompt toolkit, and we'd like to recognise his impact by giving him
   commit rights. :ghissue:`11397`

Notables Changes

 - Major update of "latex to unicode" tab completion map (see below)

Notable New Features:

 - Restore functionality and documentation of the **sphinx directive**, which
   is now stricter (fail on error by default), gained configuration options,
   have a brand new documentation page :ref:`ipython_directive`, which need
   some cleanup. It is also now *tested* so we hope to have less regressions.
   :ghpull:`11402`

 - ``IPython.display.Video`` now supports ``width`` and ``height`` arguments,
   allowing a custom width and height to be set instead of using the video's
   width and height. :ghpull:`11353`

 - Warn when using ``HTML('<iframe>')`` instead of ``IFrame`` :ghpull:`11350`

 - Allow Dynamic switching of editing mode between vi/emacs and show
   normal/input mode in prompt when using vi. :ghpull:`11390`. Use ``%config
   TerminalInteractiveShell.editing_mode = 'vi'`` or ``%config
   TerminalInteractiveShell.editing_mode = 'emacs'`` to dynamically spwitch


Notable Fixes:

 - Fix entering of **multi-line block in terminal** IPython, and various
   crashes in the new input transformation machinery :ghpull:`11354`,
   :ghpull:`11356`, :ghpull:`11358`, these ones also fix a **Compatibility but
   with Python 3.7.1**.

 - Fix moving through generator stack in ipdb :ghpull:`11266`

 - Magics arguments now support quoting. :ghpull:`11330`

 - Re-add ``rprint`` and ``rprinte`` aliases. :ghpull:`11331`

 - Remove implicit dependency to ``ipython_genutils`` :ghpull:`11317`

 - Make ``nonlocal`` raise ``SyntaxError`` instead of silently failing in async
   mode. :ghpull:`11382`

 - Fix mishandling of magics and ``= !`` assignment just after a dedent in
   nested code blocks :ghpull:`11418`

 - Fix instructions for custom shortcuts :ghpull:`11426`


Notable Internals improvements:

 - Use of ``os.scandir`` (Python 3 only) to speedup some file system operations.
   :ghpull:`11365`

 - use ``perf_counter`` instead of ``clock`` for more precise
   timing result with ``%time`` :ghpull:`11376`

Many thanks to all the contributors and in particular to ``bartskowron``, and
``tonyfast`` who handled a pretty complicated bugs in the input machinery. We
had a number of first time contributors and maybe hacktoberfest participant that
made significant contributions, and helped us free some time to focus on more
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

Some sequence have seen their prefix removed:

 - 6 characters ``\text...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 45 characters ``\Elz...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 65 characters ``\B...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 450 characters ``\m...<tab>`` should now be inputed with ``\...<tab>`` directly,

Some sequence have seen their prefix shortened:

 - 5 characters ``\mitBbb...<tab>`` should now be inputed with ``\bbi...<tab>`` directly,
 - 52 characters ``\mit...<tab>`` should now be inputed with ``\i...<tab>`` directly,
 - 216 characters ``\mbfit...<tab>`` should now be inputed with ``\bi...<tab>`` directly,
 - 222 characters ``\mbf...<tab>`` should now be inputed with ``\b...<tab>`` directly,

A couple of character had their sequence simplified:

 - ``ð``, type ``\dh<tab>``, instead of ``\eth<tab>``
 - ``ħ``, type ``\hbar<tab>``, instead of ``\Elzxh<tab>``
 - ``ɸ``, type ``\ltphi<tab>``, instead of ``\textphi<tab>``
 - ``ϴ``, type ``\varTheta<tab>``, instead of ``\textTheta<tab>``
 - ``ℇ``, type ``\eulermascheroni<tab>``, instead of ``\Eulerconst<tab>``
 - ``ℎ``, type ``\planck<tab>``, instead of ``\Planckconst<tab>``

 - U+0336 (COMBINING LONG STROKE OVERLAY), type ``\strike<tab>``, instead of ``\Elzbar<tab>``.

A couple of sequences have been updated:

 - ``\varepsilon`` now give ``ɛ`` (GREEK SMALL LETTER EPSILON) instead of ``ε`` (GREEK LUNATE EPSILON SYMBOL),
 - ``\underbar`` now give U+0331 (COMBINING MACRON BELOW) instead of U+0332 (COMBINING LOW LINE).


.. _whatsnew700:

IPython 7.0.0
=============

Released Thursday September 27th, 2018

IPython 7 include major features improvement as you can read in the following
changelog. This is also the second major version of IPython to support only
Python 3 – starting at Python 3.4. Python 2 is still community supported
on the bugfix only 5.x branch, but we remind you that Python 2 "end of life"
is on Jan 1st 2020.

We were able to backport bug fixes to the 5.x branch thanks to our backport bot which
backported more than `70 Pull-Requests
<https://github.com/ipython/ipython/pulls?page=3&q=is%3Apr+sort%3Aupdated-desc+author%3Aapp%2Fmeeseeksdev++5.x&utf8=%E2%9C%93>`_, but there are still many PRs that required manually work, and this is an area of the project were you can easily contribute by looking for `PRs still needed backport <https://github.com/ipython/ipython/issues?q=label%3A%22Still+Needs+Manual+Backport%22+is%3Aclosed+sort%3Aupdated-desc>`_

IPython 6.x branch will likely not see any further release unless critical
bugs are found.

Make sure you have pip > 9.0 before upgrading. You should be able to update by simply running

.. code::

    pip install ipython --upgrade

.. only:: ipydev

  If you are trying to install or update an ``alpha``, ``beta``, or ``rc``
  version, use pip ``--pre`` flag.

  .. code::

      pip install ipython --upgrade --pre


Or if you have conda installed: 

.. code::
   
   conda install ipython



Prompt Toolkit 2.0
------------------

IPython 7.0+ now uses ``prompt_toolkit 2.0``, if you still need to use earlier
``prompt_toolkit`` version you may need to pin IPython to ``<7.0``.

Autowait: Asynchronous REPL
---------------------------

Staring with IPython 7.0 and on Python 3.6+, IPython can automatically await
code at top level, you should not need to access an event loop or runner
yourself. To know more read the :ref:`autoawait` section of our docs, see
:ghpull:`11265` or try the following code::

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

Integration is by default with `asyncio`, but other libraries can be configured,
like ``curio`` or ``trio``, to improve concurrency in the REPL::

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
Jupyter Protocol will need further updates of the IPykernel package.

Non-Asynchronous code
~~~~~~~~~~~~~~~~~~~~~

As the internal API of IPython is now asynchronous, IPython needs to run under
an event loop. In order to allow many workflows, (like using the :magic:`%run`
magic, or copy_pasting code that explicitly starts/stop event loop), when
top-level code is detected as not being asynchronous, IPython code is advanced
via a pseudo-synchronous runner, and may not advance pending tasks.

Change to Nested Embed
~~~~~~~~~~~~~~~~~~~~~~

The introduction of the ability to run async code had some effect on the
``IPython.embed()`` API. By default embed will not allow you to run asynchronous
code unless a event loop is specified.

Effects on Magics
~~~~~~~~~~~~~~~~~

Some magics will not work with Async, and will need updates. Contribution
welcome.

Expected Future changes
~~~~~~~~~~~~~~~~~~~~~~~

We expect more internal but public IPython function to become ``async``, and
will likely end up having a persisting event loop while IPython is running.

Thanks
~~~~~~

This took more than a year in the making, and the code was rebased a number of
time leading to commit authorship that may have been lost in the final
Pull-Request. Huge thanks to many people for contribution, discussion, code,
documentation, use-case: dalejung, danielballan, ellisonbg, fperez, gnestor,
minrk, njsmith, pganssle, tacaswell, takluyver , vidartf ... And many others.


Autoreload Improvement
----------------------

The magic :magic:`%autoreload 2 <autoreload>` now captures new methods added to
classes. Earlier, only methods existing as of the initial import were being
tracked and updated.  

This new feature helps dual environment development - Jupyter+IDE - where the
code gradually moves from notebook cells to package files, as it gets
structured.

**Example**: An instance of the class ``MyClass`` will be able to access the
method ``cube()`` after it is uncommented and the file ``file1.py`` saved on
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

A couple of unused function and methods have been deprecated and will be removed
in future versions:

  - ``IPython.utils.io.raw_print_err``
  - ``IPython.utils.io.raw_print``

  
Backwards incompatible changes
------------------------------

* The API for transforming input before it is parsed as Python code has been
  completely redesigned, and any custom input transformations will need to be
  rewritten. See :doc:`/config/inputtransforms` for details of the new API.
