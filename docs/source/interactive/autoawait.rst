
.. autoawait:

Asynchronous in REPL: Autoawait
===============================

Starting with IPython 6.0, and when user Python 3.6 and above, IPython offer the
ability to run asynchronous code from the REPL. constructs which are
:exc:`SyntaxError` s in the Python REPL can be used seamlessly in IPython.

When a supported libray is used, IPython will automatically `await` Futures
and Coroutines in the REPL. This will happen if an :ref:`await <await>` (or `async`) is
use at top level scope, or if any structure valid only in `async def
<https://docs.python.org/3/reference/compound_stmts.html#async-def>`_ function
context are present. For example, the following being a syntax error in the
Python REPL::

    Python 3.6.0 
    [GCC 4.2.1]
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import aiohttp
    >>> result = aiohttp.get('https://api.github.com')
    >>> response = await result
      File "<stdin>", line 1
        response = await result
                              ^
    SyntaxError: invalid syntax

Should behave as expected in the IPython REPL::

    Python 3.6.0
    Type 'copyright', 'credits' or 'license' for more information
    IPython 6.0.0.dev -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import aiohttp
       ...: result = aiohttp.get('https://api.github.com')

    In [2]: response = await result
    <pause for a few 100s ms>

    In [3]: await response.json()
    Out[3]:
    {'authorizations_url': 'https://api.github.com/authorizations',
     'code_search_url': 'https://api.github.com/search/code?q={query}...',
    ...
    }


You can use the ``c.InteractiveShell.autoawait`` configuration option and set it
to :any:`False` to deactivate automatic wrapping of asynchronous code. You can also
use the :magic:`%autoawait` magic to toggle the behavior at runtime::

    In [1]: %autoawait False

    In [2]: %autoawait
    IPython autoawait is `Off`, and set to use `IPython.core.interactiveshell._asyncio_runner`



By default IPython will assume integration with Python's provided
:mod:`asyncio`, but integration with other libraries is provided. In particular
we provide experimental integration with the ``curio`` and ``trio`` library.

You can switch current integration by using the
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
other features of IPython and various registered extensions. In particular if you
are a direct or indirect user of the AST transformers, these may not apply to
your code.

The default loop, or runner does not run in the background, so top level
asynchronous code must finish for the REPL to allow you to enter more code. As
with usual Python semantic, the awaitables are started only when awaited for the
first time. That is to say, in first example, no network request is done between
``In[1]`` and ``In[2]``.


Internals
=========

As running asynchronous code is not supported in interactive REPL as of Python
3.6 we have to rely to a number of complex workaround to allow this to happen.
It is interesting to understand how this works in order to understand potential
bugs, or provide a custom runner.

Among the many approaches that are at our disposition, we find only one that
suited out need. Under the hood we :ct the code object from a async-def function
and run it in global namesapace after modifying the ``__code__`` object.::

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
one name space. Second, user code runs in a function scope, and not a module
scope.

On top of the above there are significant modification to the AST of
``function``, and ``loop_runner`` can be arbitrary complex. So there is a
significant overhead to this kind of code.

By default the generated coroutine function will be consumed by Asyncio's
``loop_runner = asyncio.get_evenloop().run_until_complete()`` method. It is
though possible to provide your own.

A loop runner is a *synchronous*  function responsible from running a coroutine
object.

The runner is responsible from ensuring that ``coroutine`` run to completion,
and should return the result of executing the coroutine. Let's write a
runner for ``trio`` that print a message when used as an exercise, ``trio`` is
special as it usually prefer to run a function object and make a coroutine by
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
relatively young subject. Feel free to contribute improvements to this codebase
and give us feedback.
