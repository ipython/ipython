.. _autoawait:

Asynchronous in REPL: Autoawait
===============================

.. note::

   This feature is experimental and behavior can change between python and
   IPython version without prior deprecation.

Starting with IPython 7.0, and when using Python 3.6 and above, IPython offer the
ability to run asynchronous code from the REPL. Constructs which are
:exc:`SyntaxError` s in the Python REPL can be used seamlessly in IPython.

The examples given here are for terminal IPython, running async code in a
notebook interface or any other frontend using the Jupyter protocol needs
IPykernel version 5.0 or above. The details of how async code runs in IPykernel
will differ between IPython, IPykernel and their versions.

When a supported library is used, IPython will automatically allow Futures and
Coroutines in the REPL to be ``await`` ed. This will happen if an :ref:`await
<await>` (or any other async constructs like async-with, async-for) is used at
top level scope, or if any structure valid only in `async def
<https://docs.python.org/3/reference/compound_stmts.html#async-def>`_ function
context are present. For example, the following being a syntax error in the
Python REPL::

    Python 3.6.0 
    [GCC 4.2.1]
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import aiohttp
    >>> session = aiohttp.ClientSession()
    >>> result = session.get('https://api.github.com')
    >>> response = await result
      File "<stdin>", line 1
        response = await result
                              ^
    SyntaxError: invalid syntax

Should behave as expected in the IPython REPL::

    Python 3.6.0
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.0.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import aiohttp
       ...: session = aiohttp.ClientSession()
       ...: result = session.get('https://api.github.com')

    In [2]: response = await result
    <pause for a few 100s ms>

    In [3]: await response.json()
    Out[3]:
    {'authorizations_url': 'https://api.github.com/authorizations',
     'code_search_url': 'https://api.github.com/search/code?q={query}...',
    ...
    }


You can use the ``c.InteractiveShell.autoawait`` configuration option and set it
to :any:`False` to deactivate automatic wrapping of asynchronous code. You can
also use the :magic:`%autoawait` magic to toggle the behavior at runtime::

    In [1]: %autoawait False

    In [2]: %autoawait
    IPython autoawait is `Off`, and set to use `asyncio`



By default IPython will assume integration with Python's provided
:mod:`asyncio`, but integration with other libraries is provided. In particular
we provide experimental integration with the ``curio`` and ``trio`` library.

You can switch the current integration by using the
``c.InteractiveShell.loop_runner`` option or the ``autoawait <name
integration>`` magic.

For example::

    In [1]: %autoawait trio

    In [2]: import trio

    In [3]: async def child(i):
       ...:     print("   child %s goes to sleep"%i)
       ...:     await trio.sleep(2)
       ...:     print("   child %s wakes up"%i)

    In [4]: print('parent start')
       ...: async with trio.open_nursery() as n:
       ...:     for i in range(5):
       ...:         n.spawn(child, i)
       ...: print('parent end')
    parent start
       child 2 goes to sleep
       child 0 goes to sleep
       child 3 goes to sleep
       child 1 goes to sleep
       child 4 goes to sleep
       <about 2 seconds pause>
       child 2 wakes up
       child 1 wakes up
       child 0 wakes up
       child 3 wakes up
       child 4 wakes up
    parent end


In the above example, ``async with`` at top level scope is a syntax error in
Python.

Using this mode can have unexpected consequences if used in interaction with
other features of IPython and various registered extensions. In particular if
you are a direct or indirect user of the AST transformers, these may not apply
to your code.

When using command line IPython, the default loop (or runner) does not process
in the background, so top level asynchronous code must finish for the REPL to
allow you to enter more code. As with usual Python semantics, the awaitables are
started only when awaited for the first time. That is to say, in first example,
no network request is done between ``In[1]`` and ``In[2]``.


Effects on IPython.embed()
--------------------------

IPython core being asynchronous, the use of ``IPython.embed()`` will now require
a loop to run. By default IPython will use a fake coroutine runner which should
allow ``IPython.embed()`` to be nested. Though this will prevent usage of the
:magic:`%autoawait` feature when using IPython embed. 

You can set a coroutine runner explicitly for ``embed()`` if you want to run
asynchronous code, though the exact behavior is undefined.

Effects on Magics
-----------------

A couple of magics (``%%timeit``, ``%timeit``, ``%%time``, ``%%prun``) have not
yet been updated to work with asynchronous code and will raise syntax errors
when trying to use top-level ``await``. We welcome any contribution to help fix
those, and extra cases we haven't caught yet. We hope for better support in Core
Python for top-level Async code.

Internals
---------

As running asynchronous code is not supported in interactive REPL (as of Python
3.7) we have to rely to a number of complex workarounds and heuristics to allow
this to happen. It is interesting to understand how this works in order to
comprehend potential bugs, or provide a custom runner.

Among the many approaches that are at our disposition, we find only one that
suited out need. Under the hood we use the code object from a async-def function
and run it in global namespace after modifying it to not create a new
``locals()`` scope::

    async def inner_async():
        locals().update(**global_namespace)
        #
        # here is user code
        #
        return last_user_statement
    codeobj = modify(inner_async.__code__)
    coroutine = eval(codeobj, user_ns)
    display(loop_runner(coroutine))



The first thing you'll notice is that unlike classical ``exec``, there is only
one namespace. Second, user code runs in a function scope, and not a module
scope.

On top of the above there are significant modification to the AST of
``function``, and ``loop_runner`` can be arbitrary complex. So there is a
significant overhead to this kind of code.

By default the generated coroutine function will be consumed by Asyncio's
``loop_runner = asyncio.get_evenloop().run_until_complete()`` method if
``async`` mode is deemed necessary, otherwise the coroutine will just be
exhausted in a simple runner. It is possible, though, to change the default
runner.

A loop runner is a *synchronous*  function responsible from running a coroutine
object.

The runner is responsible for ensuring that ``coroutine`` runs to completion,
and it should return the result of executing the coroutine. Let's write a
runner for ``trio`` that print a message when used as an exercise, ``trio`` is
special as it usually prefers to run a function object and make a coroutine by
itself, we can get around this limitation by wrapping it in an async-def without
parameters and passing this value to ``trio``::


    In [1]: import trio
       ...: from types import CoroutineType
       ...:
       ...: def trio_runner(coro:CoroutineType):
       ...:     print('running asynchronous code')
       ...:     async def corowrap(coro):
       ...:         return await coro
       ...:     return trio.run(corowrap, coro)

We can set it up by passing it to ``%autoawait``::

    In [2]: %autoawait trio_runner

    In [3]: async def async_hello(name):
       ...:     await trio.sleep(1)
       ...:     print(f'Hello {name} world !')
       ...:     await trio.sleep(1)

    In [4]: await async_hello('async')
    running asynchronous code
    Hello async world !


Asynchronous programming in python (and in particular in the REPL) is still a
relatively young subject. We expect some code to not behave as you expect, so
feel free to contribute improvements to this codebase and give us feedback.

We invite you to thoroughly test this feature and report any unexpected behavior
as well as propose any improvement.

Using Autoawait in a notebook (IPykernel)
-----------------------------------------

Update ipykernel to version 5.0 or greater::

   pip install ipykernel ipython --upgrade
   # or
   conda install ipykernel ipython --upgrade

This should automatically enable :magic:`autoawait` integration. Unlike
terminal IPython, all code runs on ``asyncio`` eventloop, so creating a loop by
hand will not work, including with magics like :magic:`%run` or other
frameworks that create the eventloop themselves. In cases like these you can
try to use projects like `nest_asyncio
<https://github.com/erdewit/nest_asyncio>`_ and follow `this discussion
<https://github.com/jupyter/notebook/issues/3397#issuecomment-419386811>`_

Difference between terminal IPython and IPykernel
-------------------------------------------------

The exact asynchronous code running behavior varies between Terminal IPython and
IPykernel. The root cause of this behavior is due to IPykernel having a
*persistent* `asyncio` loop running, while Terminal IPython starts and stops a
loop for each code block. This can lead to surprising behavior in some cases if
you are used to manipulating asyncio loop yourself, see for example
:ghissue:`11303` for a longer discussion but here are some of the astonishing
cases.

This behavior is an implementation detail, and should not be relied upon. It can
change without warnings in future versions of IPython.

In terminal IPython a loop is started for each code blocks only if there is top
level async code::

   $ ipython
   In [1]: import asyncio
      ...: asyncio.get_event_loop()
   Out[1]: <_UnixSelectorEventLoop running=False closed=False debug=False>

   In [2]:

   In [2]: import asyncio
      ...: await asyncio.sleep(0)
      ...: asyncio.get_event_loop()
   Out[2]: <_UnixSelectorEventLoop running=True closed=False debug=False>

See that ``running`` is ``True`` only in the case were we ``await sleep()``

In a Notebook, with ipykernel the asyncio eventloop is always running::

   $ jupyter notebook
   In [1]: import asyncio
      ...: loop1 = asyncio.get_event_loop()
      ...: loop1
   Out[1]: <_UnixSelectorEventLoop running=True closed=False debug=False>

   In [2]: loop2 = asyncio.get_event_loop()
      ...: loop2
   Out[2]: <_UnixSelectorEventLoop running=True closed=False debug=False>

   In [3]: loop1 is loop2
   Out[3]: True

In Terminal IPython background tasks are only processed while the foreground
task is running, if and only if the foreground task is async::

   $ ipython
   In [1]: import asyncio
      ...:
      ...: async def repeat(msg, n):
      ...:     for i in range(n):
      ...:         print(f"{msg} {i}")
      ...:         await asyncio.sleep(1)
      ...:     return f"{msg} done"
      ...:
      ...: asyncio.ensure_future(repeat("background", 10))
   Out[1]: <Task pending coro=<repeat() running at <ipython-input-1-02d0ef250fe7>:3>>

   In [2]: await asyncio.sleep(3)
   background 0
   background 1
   background 2
   background 3

   In [3]: import time
   ...: time.sleep(5)

   In [4]: await asyncio.sleep(3)
   background 4
   background 5
   background 6g

In a Notebook, QtConsole, or any other frontend using IPykernel, background
tasks should behave as expected.
