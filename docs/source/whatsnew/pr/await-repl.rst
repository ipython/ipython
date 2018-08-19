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


Change to Nested Embed
----------------------

The introduction of the ability to run async code had ripple effect on the
ability to use nested IPython. You may need to install the ``trio`` library
(version 0.5 at the time of this writing) to
have this feature working. 


