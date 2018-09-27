============
 7.x Series
============

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

As the internal API of IPython are now asynchronous, IPython need to run under
an even loop. In order to allow many workflow, (like using the :magic:`%run`
magic, or copy_pasting code that explicitly starts/stop event loop), when
top-level code is detected as not being asynchronous, IPython code is advanced
via a pseudo-synchronous runner, and will not may not advance pending tasks.

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


..code::

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


The :cellmagic:`%%script`` (as well as :cellmagic:`%%bash``,
:cellmagic:`%%ruby``... ) cell magics now raise by default if the return code of
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
