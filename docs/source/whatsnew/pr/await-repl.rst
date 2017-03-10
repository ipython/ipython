Await REPL
----------

:ghpull:`10390` introduced the ability to ``await`` Asyncio Futures and
Coroutines in the REPL. This will happen automatically if an ``await`` is use at
top level scope or if any structures that are valid only in `async def
<https://docs.python.org/3/reference/compound_stmts.html#async-def>`_ function
context should triggered this mode. For example::

    Python 3.6.0
    Type 'copyright', 'credits' or 'license' for more information
    IPython 6.0.0.dev -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import aiohttp
       ...: result = aiohttp.get('https://api.github.com')

    In [2]: response = await result

    In [3]: await response.json()
    Out[3]:
    {'authorizations_url': 'https://api.github.com/authorizations',
     'code_search_url': 'https://api.github.com/search/code?q={query}{&page,per_page,sort,order}',
    ...
    }


Under the hood we wrap user code in an ``async def`` block, and patch the global
namespace back. By default the wrapped function will be consumed by Asyncio's
``run_until_complete()`` method.

Using this mode can have unexpected consequences if used in interaction with
other features of IPython and various register extension. In particular if you
are a direct or indirect user of the AST transformers, these may not apply to
your code if it contains top level await, or break the automatic running.

You can use the ``c.InteractiveShell.autoawait`` configuration option and set it
to ``False`` to deactivate this behavior.

If you wish to use a different loop runner,.....

