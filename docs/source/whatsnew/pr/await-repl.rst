Await REPL
----------

:ghpull:`10390` introduced the ability to ``await`` Futures and
Coroutines in the REPL. This will happen automatically if an ``await`` is use at
top level scope or if any structures that are valid only in `async def
<https://docs.python.org/3/reference/compound_stmts.html#async-def>`_ function
context are used. For example::

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
     'code_search_url': 'https://api.github.com/search/code?q={query}{&page,per_page,sort,order}',
    ...
    }


Under the hood we wrap user code in an ``async def`` block, and patch the global
namespace back. By default the wrapped function will be consumed by Asyncio's
``run_until_complete()`` method. Though you can set the
``--InteractiveShell.looprunner`` option to provide your own runner. 
Thus with custon configuration it is possible to use ``curio`` or ``trio``.
For example::

    In [1]: import trio

    In [2]: async def child(i):
       ...:     print("   child %s goes to sleep"%i)
       ...:     await trio.sleep(2)
       ...:     print("   child %s wakes up"%i)

    In [3]: print('parent start')
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
your code if it contains top level await, or break the automatic running.

You can use the ``c.InteractiveShell.autoawait`` configuration option and set it
to ``False`` to deactivate automatic wrapping of asynchronous code.

The default loop does not run in the background, so your asynchronous code must
finish for the REPL to allow you to enter more code. As with usual Python
semantic, the awaitables are started only when awaited for the first time. That
is to say, in first example, no network request is done between ``In[1]`` and
``In[2]``

