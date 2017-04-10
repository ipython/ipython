"""
Async helper function that are invalid syntax on Python 3.5 and below.

Known limitation and possible improvement. 

Top level code that contain a return statement (instead of, or in addition to
await) will be detected as requiring being wrapped in async calls. This should
be prevented as early return will not work.
"""



import ast
import sys
import inspect
from textwrap import dedent, indent
from types import CodeType

def _asyncio_runner(coro):
    """
    Handler for asyncio autoawait
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)

def _curio_runner(coroutine):
    """
    handler for curio autoawait
    """
    import curio
    return curio.run(coroutine)

if sys.version_info > (3,5):
    # nose refuses to avoid this file and async def is invalidsyntax
    s = dedent('''
    def _trio_runner(function):
        import trio
        async def loc(coro):
            """
            We need the dummy no-op async def to protect from
            trio's internal. See https://github.com/python-trio/trio/issues/89
            """
            return await coro
        return trio.run(loc, function)
    ''')
    exec(s, globals(), locals())

def _asyncify(code:str) -> str:
    """wrap code in async def definition.

    And setup a bit of context to run it later.
    """
    res = dedent("""
        async def ___wrapper___():
            {usercode}
            locals()
            return None
        """).format(usercode=indent(code,' '*4)[4:])
    return res

def _should_be_async(cell:str) -> bool:
    """Detect if a block of code need to be wrapped in an `async def`

    Attempt to parse the block of code, it it compile we're fine.
    Otherwise we  wrap if and try to compile.

    If it works, assume it should be async. Otherwise Return False.

    Not handled yet: If the block of code has a return statement as  the top
    level, it will be seen as async. This is a know limitation.
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
