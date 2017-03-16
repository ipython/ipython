"""
Async helper function that are invalid syntax on Python 3.5 and below.

Known limitation and possible improvement. 

Top level code that contain a return statement (instead of, or in addition to
await) will be detected as requiring being wrapped in async calls. This should
be prevented as early return will not work.
"""



import ast
import sys
from textwrap import dedent, indent

def _asyncio_runner(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)

def _curio_runner(function, user_ns):
    import curio
    return curio.run(function(**user_ns))

if sys.version_info > (3,5):
    # nose refuses to avoid this file.
    s = dedent('''
    def _trio_runner(function, user_ns):
        import trio
        async def loc(fun, user_ns):
            """
            We need the dummy no-op async def to protect from
            trio's internal. See https://github.com/python-trio/trio/issues/89
            """
            return await fun(**user_ns)
        return trio.run(loc, function, user_ns)
    ''')
    exec(s, globals(), locals())

def _asyncify(code):
    """wrap code in async def definition.

    And setup a bit of context to run it later.

    The following names are part of the API:

     - ``user_ns`` is used as the name for the namespace to run code in, both
     _in_ and _out_.
     - ``loop_runner`` is use to send the loop_runner _in_
     - ``last_expression`` to get the last expression _out_
    """
    res = dedent("""
        async def phony():
            {usercode}
            locals()
        """).format(usercode=indent(code,' '*4)[4:])
    return res

def _should_be_async(cell:str) -> bool:
    """Detect if a block of code need to be wrapped in an `async def`

    Attempt to parse the block of code, it it compile we're fine.
    Otherwise we  wrap if and try to compile.

    If it works, assume it should be async. Otherwise Return False.
    """
    try:
        ast.parse(cell)
        return False
    except SyntaxError:
        try:
            ast.parse(_asyncify(cell))
        except SyntaxError:
            return False
        return True
    return False

